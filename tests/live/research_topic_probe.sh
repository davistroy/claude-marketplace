#!/usr/bin/env bash
#
# research_topic_probe.sh -- MANUAL, OWNER-RUN ONLY. Do not add to CI.
#
# CI holds ZERO secrets (ADR-0009/D32) and therefore cannot supply
# ANTHROPIC_API_KEY, so this probe is never wired into any GitHub Actions
# workflow (see IMPLEMENTATION_PLAN.md 6.5, DoD row "Probe is not CI-wired").
# It exists to verify the shipped Anthropic Claude research leg
# (plugins/personal-plugin/references/research-provider-protocols.md +
# plugins/personal-plugin/tools/research-sse) against the REAL Anthropic API.
#
# Run it by hand:
#   ANTHROPIC_API_KEY=sk-ant-... bash tests/live/research_topic_probe.sh
#
# With no key set, the offline preflight (research-sse's own bundled
# fixtures, no network, no secret) still runs, and the live leg is SKIPPED
# CLEANLY (exit 0), not failed -- so this script is always safe to run.
#
# WHY THIS DERIVES RATHER THAN RESTATES THE REQUEST SHAPE:
# A prior version of this probe extracted the request body and the depth
# ladder directly out of the shipped reference files, which is what made it
# impossible for the probe to pass while those files were broken. That
# probe was never committed -- this is the replacement, kept honest the
# same way. Every value used below (model name, `effort`, `max_tokens`, the
# request JSON shape, and the full curl/PIPESTATUS/exit-code handling
# logic) is parsed at run time out of:
#   - plugins/personal-plugin/references/research-provider-protocols.md
#   - plugins/personal-plugin/references/research-models.md
# Nothing about the request shape or the depth ladder is hand-typed here.
# If either file's structure drifts far enough that the extraction regexes
# no longer match, this script fails loudly (EXTRACT-FAIL) rather than
# silently falling back to a restated copy.
#
# Negative control: the extracted request is corrupted by reintroducing
# `thinking.budget_tokens`, the exact removed parameter the protocol file
# documents as returning HTTP 400 on every current model. If that corrupted
# request somehow succeeds, this script reports FAIL -- a negative control
# that cannot fail proves only that the network works.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PLUGIN_DIR="$REPO_ROOT/plugins/personal-plugin"
PROTOCOL_FILE="$PLUGIN_DIR/references/research-provider-protocols.md"
MODELS_FILE="$PLUGIN_DIR/references/research-models.md"
TOOL_SRC="$PLUGIN_DIR/tools/research-sse/src"
FIXTURES_DIR="$PLUGIN_DIR/tools/research-sse/tests/fixtures"

OVERALL_FAIL=0

echo "=== research_topic_probe.sh (manual/owner-run; CI holds no secrets, ADR-0009/D32) ==="

# --- Phase 0: sanity ---------------------------------------------------
for bin in python3 curl bash; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "FAIL: required binary '$bin' not found on PATH" >&2
    exit 1
  fi
done
for f in "$PROTOCOL_FILE" "$MODELS_FILE"; do
  if [ ! -f "$f" ]; then
    echo "FAIL: shipped file not found: $f" >&2
    exit 1
  fi
done
if [ ! -d "$TOOL_SRC" ]; then
  echo "FAIL: research-sse source not found: $TOOL_SRC" >&2
  exit 1
fi

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

# --- Phase 1: offline preflight -- research-sse's own fixtures, no key -
echo "--- Phase 1: offline preflight (research-sse bundled fixtures, no API key) ---"

check_fixture() {
  # $1=fixture file  $2=expected exit code  $3=label
  local file="$1" want="$2" label="$3" err code
  err=$(PYTHONPATH="$TOOL_SRC" python3 -m research_sse --input "$file" --quiet 2>&1 >/dev/null)
  code=$?
  if [ "$code" -ne "$want" ]; then
    echo "FAIL: $label -- expected exit $want, got $code: $err" >&2
    return 1
  fi
  echo "ok: $label -- exit=$code as expected"
  return 0
}

PREFLIGHT_FAIL=0
check_fixture "$FIXTURES_DIR/happy_path.sse" 0 "happy_path.sse (normal completion)" || PREFLIGHT_FAIL=1
check_fixture "$FIXTURES_DIR/refusal_with_category.sse" 4 "refusal_with_category.sse (safety refusal)" || PREFLIGHT_FAIL=1
check_fixture "$FIXTURES_DIR/truncation_max_tokens.sse" 0 "truncation_max_tokens.sse (truncated but kept)" || PREFLIGHT_FAIL=1
check_fixture "$FIXTURES_DIR/no_terminal_event.sse" 5 "no_terminal_event.sse (mid-flight death)" || PREFLIGHT_FAIL=1

if [ "$PREFLIGHT_FAIL" -ne 0 ]; then
  echo "FAIL: offline preflight failed -- research-sse itself is broken; not attempting the live leg" >&2
  exit 1
fi

# --- Phase 2: derive the request shape + depth ladder from shipped files
echo "--- Phase 2: deriving request shape + depth ladder from shipped files (offline) ---"

if ! python3 - "$PROTOCOL_FILE" "$MODELS_FILE" "$TMPDIR" <<'PYEOF'
import json
import os
import re
import sys

protocol_path, models_path, tmpdir = sys.argv[1], sys.argv[2], sys.argv[3]
protocol_text = open(protocol_path, encoding="utf-8").read()
models_text = open(models_path, encoding="utf-8").read()


def fail(msg):
    print(f"EXTRACT-FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


# 1. Isolate the Anthropic Claude Protocol section.
m = re.search(r"^## Anthropic Claude Protocol\n(.*?)(?=^## )", protocol_text, re.S | re.M)
if not m:
    fail("could not locate '## Anthropic Claude Protocol' in research-provider-protocols.md")
section = m.group(1)

# 2. Extract the Request bash block: the fenced ```bash block containing the
#    curl -d request body. This is the shipped code, verbatim -- not a
#    reimplementation of it.
blocks = re.findall(r"```bash\n(.*?)\n```", section, re.S)
request_block = next((b for b in blocks if "-d '{" in b), None)
if request_block is None:
    fail("no ```bash block in the Anthropic section contains a `-d '{` request body -- shape changed")

# 3. Extract the raw JSON payload template for an offline shape check before
#    ever touching the network.
pm = re.search(r"-d '(\{.*?\})'\s*2>", request_block, re.S)
if not pm:
    fail("could not isolate the JSON payload passed to curl -d -- request shape changed")
payload_template = pm.group(1)

for required in ('"stream": true', '"thinking"', '"type": "adaptive"', '"output_config"', '"effort"'):
    if required not in payload_template:
        fail(f"extracted request payload is missing {required!r} -- shipped shape changed")
if "budget_tokens" in payload_template:
    fail("shipped request payload already contains budget_tokens -- removed-parameter regression")

# 4. Extract the depth ladder's Brief row from research-models.md.
dm = re.search(r"^## Depth Parameter Mapping\n(.*?)(?=^## |\Z)", models_text, re.S | re.M)
if not dm:
    fail("could not locate '## Depth Parameter Mapping' in research-models.md")
depth_section = dm.group(1)

header_line = next(
    (ln for ln in depth_section.splitlines() if ln.strip().startswith("|") and "Anthropic effort" in ln),
    None,
)
if not header_line:
    fail("could not find the Depth Parameter Mapping header row")
headers = [c.strip() for c in header_line.strip().strip("|").split("|")]
try:
    effort_idx = headers.index("Anthropic effort")
    tokens_idx = headers.index("Anthropic max_tokens")
except ValueError:
    fail(f"Depth Parameter Mapping header is missing an expected column: {headers!r}")

brief_line = next((ln for ln in depth_section.splitlines() if ln.strip().startswith("| Brief")), None)
if not brief_line:
    fail("no 'Brief' row in the Depth Parameter Mapping table")
cells = [c.strip() for c in brief_line.strip().strip("|").split("|")]
if len(cells) <= max(effort_idx, tokens_idx):
    fail(f"Brief row has fewer columns than the header: {cells!r}")
effort = cells[effort_idx]
max_tokens = cells[tokens_idx].replace(",", "")
if not effort or not max_tokens.isdigit():
    fail(f"Brief row extracted unusable values: effort={effort!r} max_tokens={cells[tokens_idx]!r}")

# 5. Extract the default Anthropic model name.
dn = re.search(r"^## Default Model Names\n(.*?)(?=^## |\Z)", models_text, re.S | re.M)
if not dn:
    fail("could not locate '## Default Model Names' in research-models.md")
name_section = dn.group(1)
name_header = next(
    (ln for ln in name_section.splitlines() if ln.strip().startswith("|") and "Default Value" in ln), None
)
if not name_header:
    fail("could not find the Default Model Names header row")
name_headers = [c.strip() for c in name_header.strip().strip("|").split("|")]
try:
    default_idx = name_headers.index("Default Value")
except ValueError:
    fail(f"Default Model Names header is missing 'Default Value': {name_headers!r}")
anthropic_line = next((ln for ln in name_section.splitlines() if ln.strip().startswith("| Anthropic")), None)
if not anthropic_line:
    fail("no 'Anthropic' row in the Default Model Names table")
name_cells = [c.strip() for c in anthropic_line.strip().strip("|").split("|")]
model = name_cells[default_idx].strip("`")
if not model:
    fail("extracted Anthropic default model name is empty")

# 6. Build the substituted (positive) and corrupted (negative) scripts.
prompt = "Reply with exactly the single word: probe-ok"


def substitute(block, timestamp):
    out = block
    out = out.replace("[TIMESTAMP]", timestamp)
    out = out.replace("[RESOLVED_CLAUDE_MODEL]", model)
    out = out.replace("[MAX_TOKENS]", max_tokens)
    out = out.replace("[EFFORT]", effort)
    out = out.replace("[ESCAPED RESEARCH PROMPT]", prompt)
    return out


pid = os.getpid()
positive = substitute(request_block, f"probe-pos-{pid}")
negative_source = substitute(request_block, f"probe-neg-{pid}")

# Negative control: reintroduce the removed `thinking.budget_tokens`
# parameter -- the exact regression the protocol file documents as
# returning HTTP 400 on every current model. The corruption target is
# located inside the just-substituted text, not assumed in the abstract.
neg_pattern = re.compile(r'("type":\s*"adaptive")(\s*\n\s*\})')
if not neg_pattern.search(negative_source):
    fail("could not locate the thinking.adaptive object to corrupt for the negative control")
negative = neg_pattern.sub(r'\1,\n      "budget_tokens": 1024\2', negative_source, count=1)
if "budget_tokens" not in negative:
    fail("negative-control corruption did not take effect")

remaining = [
    tok
    for tok in ("[TIMESTAMP]", "[RESOLVED_CLAUDE_MODEL]", "[MAX_TOKENS]", "[EFFORT]", "[ESCAPED RESEARCH PROMPT]")
    if tok in positive or tok in negative
]
if remaining:
    fail(f"unsubstituted placeholders remain after substitution: {remaining!r}")

# 7. Offline validity check: the substituted JSON must actually parse, and
#    must carry exactly the extracted ladder values -- catches a shape bug
#    before ever spending a live API call on it.
pm_pos = re.search(r"-d '(\{.*?\})'\s*2>", positive, re.S)
if not pm_pos:
    fail("could not re-isolate the substituted positive JSON payload")
try:
    parsed_pos = json.loads(pm_pos.group(1))
except json.JSONDecodeError as exc:
    fail(f"substituted positive payload is not valid JSON: {exc}")
if parsed_pos.get("thinking", {}).get("type") != "adaptive":
    fail("substituted positive payload lost thinking.type=adaptive")
if "budget_tokens" in parsed_pos.get("thinking", {}):
    fail("substituted positive payload unexpectedly contains budget_tokens")
if parsed_pos.get("output_config", {}).get("effort") != effort:
    fail("substituted positive payload effort does not match the extracted ladder value")
if parsed_pos.get("max_tokens") != int(max_tokens):
    fail("substituted positive payload max_tokens does not match the extracted ladder value")

pm_neg = re.search(r"-d '(\{.*?\})'\s*2>", negative, re.S)
if not pm_neg:
    fail("could not re-isolate the substituted negative JSON payload")
try:
    parsed_neg = json.loads(pm_neg.group(1))
except json.JSONDecodeError as exc:
    fail(f"substituted negative payload is not valid JSON: {exc}")
if "budget_tokens" not in parsed_neg.get("thinking", {}):
    fail("negative-control payload does not carry the reintroduced budget_tokens key")

with open(os.path.join(tmpdir, "positive.sh"), "w", encoding="utf-8") as fh:
    fh.write("#!/usr/bin/env bash\nset -uo pipefail\n" + positive + "\n")
with open(os.path.join(tmpdir, "negative.sh"), "w", encoding="utf-8") as fh:
    fh.write("#!/usr/bin/env bash\nset -uo pipefail\n" + negative + "\n")

print(f"derived: model={model} effort={effort} max_tokens={max_tokens}")
print("EXTRACT-OK")
PYEOF
then
  echo "FAIL: derivation step failed -- shipped files have drifted out of shape (see EXTRACT-FAIL above)" >&2
  exit 1
fi

# --- Phase 3: skip cleanly if no key is present -------------------------
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "SKIP: ANTHROPIC_API_KEY not set -- live leg skipped cleanly (offline checks all passed)"
  exit 0
fi

export CLAUDE_PLUGIN_ROOT="$PLUGIN_DIR"
chmod +x "$TMPDIR/positive.sh" "$TMPDIR/negative.sh"

# --- Phase 4: live positive control (real API call, Brief depth) --------
echo "--- Phase 4: live positive control (real Anthropic API call, Brief depth) ---"
bash "$TMPDIR/positive.sh"
POS_EXIT=$?
echo "positive control exit=$POS_EXIT (want 0)"

# --- Phase 5: live negative control (reintroduced budget_tokens) --------
echo "--- Phase 5: live negative control (reintroduced thinking.budget_tokens, must fail) ---"
bash "$TMPDIR/negative.sh"
NEG_EXIT=$?
echo "negative control exit=$NEG_EXIT (want nonzero)"

if [ "$POS_EXIT" -ne 0 ]; then
  echo "FAIL: positive control did not succeed (exit=$POS_EXIT) -- the shipped Claude leg is broken" >&2
  OVERALL_FAIL=1
fi
if [ "$NEG_EXIT" -eq 0 ]; then
  echo "FAIL: negative control succeeded -- the reintroduced budget_tokens should have been rejected by the API" >&2
  OVERALL_FAIL=1
fi

if [ "$OVERALL_FAIL" -ne 0 ]; then
  exit 1
fi

echo "PASS: shipped Claude research leg verified live; negative control failed as designed"
exit 0
