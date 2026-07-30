# personal-plugin Eval Suite

Structured test specifications for every command and skill in `personal-plugin`. Each eval defines concrete scenarios, pass/fail criteria, and a quality rubric — so you can verify that commands behave as specified after edits, refactors, or model upgrades.

## Structure

```
evals/
  README.md                    # This file
  fixtures/
    docs/                      # Sample input documents
      sample-prd.md            # Well-formed PRD (~3.5-4.5 quality score)
      draft-prd.md             # Incomplete PRD with TBDs and gaps (~2-3 score)
      meeting-transcript.md    # Team meeting with action items and decisions
      ip-document.md           # Doc containing company identifiers (for remove-ip)
      multi-variant-a.md       # API design doc — REST perspective (for consolidate)
      multi-variant-b.md       # API design doc — GraphQL perspective (for consolidate)
    json/
      questions-sample.json    # Pre-extracted questions (for ask-questions)
    plans/
      implementation-plan.md   # Sample IMPLEMENTATION_PLAN.md (for implement-plan)
  commands/
    *.eval.md                  # One eval file per command
  skills/
    *.eval.md                  # One eval file per skill
```

## Eval File Format

Each eval file contains:

```markdown
---
command: <name>
type: command|skill
fixtures: [list of required fixtures]
---
```

`command: <name>` must match a live skill (`plugins/*/skills/<name>/SKILL.md`)
or command (`plugins/*/commands/<name>.md`) somewhere in the repo — this is
enforced in CI (see "Eval-Mapping Check" below).

A small number of eval files intentionally exercise multiple skills/commands
at once instead of one (e.g. `description-triggers.eval.md`, which
regression-guards auto-invocation across several unrelated skills). These
declare `type: cross-cutting` and a `maps_to: [name1, name2, ...]` list in
place of a single `command:` target. `command:` is still required on a
cross-cutting eval, but it is not a live-surface reference (`maps_to` is) —
it must equal the eval's own filename slug (`description-triggers.eval.md`
→ `command: description-triggers`), so the field can never silently go
blank or drift:

```markdown
---
command: description-triggers
type: cross-cutting
fixtures: []
maps_to: [skill-a, skill-b, skill-c]
---

# Eval: /<name>

## Purpose
What this command does and what "good" output looks like.

## Fixtures
Table of required fixture files and their purpose.

## Test Scenarios

### S1: <scenario name>
**Invocation:** `/command-name <args>`
**Setup:** <any preconditions>

**Must** (fail eval if any are missing):
- [ ] criterion 1

**Should** (warn if missing, don't fail):
- [ ] criterion 1

**Must NOT** (fail eval if present):
- [ ] criterion 1

## Rubric
Scoring table with weights.
```

## Running Evals

Evals are designed to be executed in a live Claude Code session. They are not automated unit tests — they test LLM behavior against a behavioral contract.

### Headless Execution

Running evals unattended via `claude -p` (rather than an interactive session) surfaces four harness behaviors that are easy to misread as eval failures. These apply to every eval in this suite, not just `description-triggers`:

1. **The `Skill` tool is auto-denied in headless `claude -p` sessions** — there is no human present to approve it. A working harness needs an explicit `--allowed-tools Skill Read Write Edit Glob Grep AskUserQuestion`. Without it, a skill-invocation eval returns `is_error: true` and reads as a total behavioral failure when it is purely a permission artifact.
2. **`AskUserQuestion` is unavailable in headless `-p` sessions.** A skill that would normally ask via that tool falls back to asking in prose instead. A runner must NOT score "no `AskUserQuestion` call" as a gate failure.
3. **`api_error_status: 529` is not a result.** The first real run of `description-triggers` returned 529 on 8 of 13 scenarios; a naive scorer would have recorded 8 failures. Re-runs with backoff passed all 8. Any runner must distinguish an API error from a negative result.
4. **Score at first dispatch, not after a long budget.** A routing eval should not need a five-minute budget per scenario — one scenario hit a 300s timeout while correctly routing and then doing real (and unnecessary) work. Score which skill was dispatched to as soon as that is observable, rather than waiting for the whole turn to finish.

`claude plugin eval` (Claude Code 2.1.220+) exists natively but currently **exits 1 with "currently in early access"**, so it is unusable as a runner today. Converging this corpus onto it would mean porting all 255 scenarios and roughly 1,091 criteria from zero — about 4.6x the diff ADR-0009 already rejected — and adopting it would supersede ADR-0009 and reopen D32. It is therefore **deferred, with an explicit pointer to ADR-0009**, not scheduled; see `docs/adr/0009-eval-execution-strategy.md` before proposing a migration.

### Manual Execution

1. Open a Claude Code session in a scratch directory (not the marketplace repo)
2. Install the plugin: `/plugin marketplace add davistroy/claude-marketplace && /plugin install personal-plugin@troys-plugins`
3. Copy the relevant fixture file(s) into the scratch directory
4. Follow the invocation and setup steps in each scenario
5. Check each Must/Should/Must NOT criterion

### Batch Evaluation

To evaluate all commands systematically:

```bash
# Create a temp eval workspace
mkdir -p /tmp/eval-workspace && cd /tmp/eval-workspace
cp -r <marketplace>/evals/fixtures/* .

# Open Claude Code and run each scenario
# Track results in a spreadsheet or eval-results.md
```

### Scoring

For each scenario:
- All **Must** criteria met = PASS
- Any **Must NOT** criterion present = FAIL regardless of Must
- **Should** criteria tracked separately as quality notes

For each command overall, score the Rubric criteria and record:
- PASS (all Must met, no Must NOT triggered)
- PARTIAL (some Must missing, no Must NOT)
- FAIL (Must NOT triggered, or critical Must missing)

## Fixture Descriptions

| Fixture | Description | Commands That Use It |
|---------|-------------|----------------------|
| `docs/sample-prd.md` | Well-formed PRD for "Daily Standup Bot" | assess-document, define-questions, create-plan, review-intent |
| `docs/draft-prd.md` | Incomplete PRD with TBDs, questions, vague requirements | assess-document, define-questions, finish-document, create-plan |
| `docs/meeting-transcript.md` | 20-min kickoff meeting with action items and decisions | analyze-transcript |
| `docs/ip-document.md` | Internal process doc with company identifiers | remove-ip |
| `docs/multi-variant-a.md` | API design doc, REST-centric | consolidate-documents |
| `docs/multi-variant-b.md` | API design doc, GraphQL-centric | consolidate-documents |
| `json/questions-sample.json` | 5 pre-extracted questions from draft-prd.md | ask-questions |
| `plans/implementation-plan.md` | 2-phase IMPLEMENTATION_PLAN.md for the standup bot | implement-plan |

## Eval-Mapping Check

`scripts/check_eval_mapping.py` (stdlib only, wired into the `plugin-validate`
CI job) runs three checks over `evals/**/*.eval.md`:

1. **Mapping** — every eval maps to something real: either its `command:`
   frontmatter matches a live skill/command, or (for `type: cross-cutting`
   files) every name in `maps_to` does. An eval can never silently outlive a
   renamed or removed skill.
2. **Structure** — every eval has at least one `### S<n>: ...` scenario, every
   scenario has a `**Must:**` or `**Must NOT:**` block, an invocation
   (`**Invocation:**` or `**Context:**`) is established at least once per
   file (later scenarios may inherit it from an earlier one), and the file
   has a `## Rubric` section.
3. **Coverage** — every live skill/command is referenced by some eval, or has
   a reasoned entry in the `COVERAGE_ALLOWLIST` dict inside the script (e.g.
   fleet-ops skills that require SSH to specific hosts, or slide-gen skills
   that require the external engine + API keys per ADR-0008).

Any failure fails the build. Run it locally with:

```bash
python3 scripts/check_eval_mapping.py
```

## Maintenance

- When a command's behavior changes, update the corresponding eval file
- When a command/skill is renamed, rename or delete its eval file (or update `maps_to`) in the same change — `check_eval_mapping.py` will fail CI otherwise
- When adding a new command or skill, add a new eval file and register the fixture if needed
- Run the full eval suite before releasing a new plugin version (`/bump-version`)
- The `/validate-plugin` command checks structure; evals check behavior
