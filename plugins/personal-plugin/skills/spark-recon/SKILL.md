---
name: spark-recon
description: Use when checking on DGX Spark inference performance landscape — scans Arena leaderboard, vLLM releases, spark-vllm-docker builds, Qwen models, and NVIDIA forum for actionable changes. Run periodically from the spark project directory.
allowed-tools: Read, Edit, Glob, Grep, Bash, Agent, WebFetch, WebSearch
paths:
  - "SPARK_BASELINE.md"
  - "*_CONFIG.md"
---

# Spark Recon

Periodic intelligence scan of the DGX Spark inference performance landscape. Five parallel checks, compared against stored baselines, classified by urgency, cross-correlated, results appended to LAB_NOTEBOOK.md.

**This skill is report + recommend only. It never touches the Spark system.**

Follow the shared execution framework, trigger logic, cross-correlation, classification, LAB_NOTEBOOK entry templates, baseline update protocol, and web research patterns defined in:
`plugins/personal-plugin/references/patterns/audit-recon-system.md`

---

## Loop Guard — Auto-Activation Safety Check

**Run this check before any other step when the skill is triggered automatically via `paths:`.**

1. Read the last 20 lines of `LAB_NOTEBOOK.md` (if it exists).
2. If any line contains `spark-recon skill` and a timestamp within the last 5 minutes: **stop immediately** — self-triggered re-entry detected. Output: "Loop guard triggered — spark-recon ran within last 5 minutes. Skipping." and exit.
3. If `--force` is present in `$ARGUMENTS`: skip this check and proceed regardless.
4. Otherwise: proceed normally.

---

## Machine Config

```yaml
machine:
  name: "DGX Spark (GB10)"
  baseline_file: "SPARK_BASELINE.md"
  project_root: "~/dev/personal/spark/"
  notebook_file: "LAB_NOTEBOOK.md"

recon_sources:
  check1_source: "https://spark-arena.com/leaderboard (browser MCP preferred; WebFetch fallback)"
  check2_source: "https://api.github.com/repos/vllm-project/vllm/releases?per_page=5"
  check3_source: "https://api.github.com/repos/eugr/spark-vllm-docker/releases?per_page=5 + commits?per_page=10"
  check4_source: "HuggingFace (MCP if available) + web search"
  check5_source: "Discourse JSON: forums.developer.nvidia.com/c/accelerated-computing/dgx-spark-gb10/{719,720,721}.json"

trigger_sources:
  vllm_release: "Check 2 (vLLM releases) release notes and changelog"
  arena: "Check 1 (Arena leaderboard) entries and tok/s values"
  huggingface: "Check 4 (Qwen model landscape) search results"
  forum: "Check 5 (NVIDIA Forum) post titles and summaries"
  svd: "Check 3 (spark-vllm-docker) commits and releases"

arena_filter: "tg128 test type, concurrency 1, single-node only"
arena_action_threshold_pct: 10   # 10%+ tok/s jump over baseline = ACTION NEEDED
current_model: "Qwen/Qwen3.5-35B-A3B"
quantization: "FP8 on-the-fly"
community_builders:
  - hellohal2064
  - Artyom
  - sus
  - sesmanovic
  - namake-taro
  - coolthor
  - sggin1
  - eugr
```

---

## Required Files

| File | Location | Purpose |
|------|----------|---------|
| `SPARK_BASELINE.md` | `~/dev/personal/spark/` | Performance numbers + last-checked dates + watch items |
| `LAB_NOTEBOOK.md` | `~/dev/personal/spark/` | Append-only results log |

If `SPARK_BASELINE.md` doesn't exist, create it using the template at the bottom of this skill.

---

## Check-Specific Instructions

Use the Generic Recon Check Structure from the shared reference. Machine-specific details below.

### Check 1 — Spark Arena Leaderboard

**Data source:** `https://spark-arena.com/leaderboard`

**Agent instructions:**
1. Open leaderboard via browser tools (`mcp__claude-in-chrome__tabs_create_mcp` → `mcp__claude-in-chrome__navigate` → `mcp__claude-in-chrome__get_page_text`). Fall back to `WebFetch` if browser unavailable.
2. Filter: **`tg128` type, concurrency 1, single-node only.** We have one DGX Spark — multi-node is informational, not actionable.
3. Find top FP8-quantized, single-node Qwen3.5 entry: name, tok/s, creator, rank.
4. Compare tok/s against baseline `arena_top_fp8_qwen35_tok_s`. If 10%+ jump: ACTION NEEDED.
5. On ACTION: fetch recipe via `https://spark-arena.com/api/recipes/{id}/raw`. Extract config diff vs SPARK_BASELINE.md (env vars, flags, container image, model variant, load-format, batch token settings).
6. Scan top 5 single-node entries overall. Flag any new non-Qwen3.5 FP8 contender.

**Return:** top FP8 Qwen3.5 single-node entry (name, tok/s, delta %), top overall, recipe diff if actionable, new contenders.

### Check 2 — vLLM Releases

**Data source:** `https://api.github.com/repos/vllm-project/vllm/releases?per_page=5`

**Agent instructions:**
1. `WebFetch` releases API. Compare against baseline `vllm_last_checked_version`.
2. Classify keywords: HIGH = `SM121`, `SM120`, `Blackwell`, `GB10`, `#38126`, `sm_12`, `arch guard`; MEDIUM = `prefix caching`, `Mamba`, `hybrid`, `MoE`, `Marlin`, `Qwen3.5`, `mixed architecture`; LOW = none of the above.
3. If HIGH: generate concrete test plan (docker run --rm command, startup log checks for SM121 kernel loading + FP8 warning, rollback note with current image tag from baseline).

**Return:** latest version, classification, relevant changelog items, test plan if HIGH.

### Check 3 — spark-vllm-docker Builds

**Data source:** releases and commits APIs (see Machine Config).

**Agent instructions:**
1. `WebFetch` releases and recent commits. This project builds `vllm-node` containers for Arena entries — new builds are a leading indicator of Arena performance jumps.
2. Look for: new container image tags, Dockerfile changes, new recipes, SM121/SM120 kernel patches, FlashInfer updates.
3. Compare against baseline `svd_last_checked_date`.
4. If new build: note base vLLM version, patches applied, target architecture.

**Return:** new releases or commits since last check, new container images, notable changes.

### Check 4 — Qwen Model Landscape

**CONTEXT: Already running `Qwen/Qwen3.5-35B-A3B` FP8. This check looks for models NEWER than Qwen3.5. Do NOT report Qwen3.5-35B-A3B as "new."**

**Agent instructions:**
1. If HuggingFace MCP available: search Qwen org, >10B parameters, created after 2026-03-01.
2. `WebSearch`: `"Qwen4" model 2026`, `Qwen new model release 2026`, `Qwen3.5 successor`.
3. Look for: new model families (Qwen4, etc.), `Qwen/Qwen3.5-35B-A3B-FP8` (pre-quantized), new fine-tunes, architecture changes.
4. For each new model: parameter count, architecture (MoE vs dense, hybrid Mamba), available quantizations, benchmarks. Flag existence + key specs — model switching is a separate decision.

**Return:** new models or "no new models beyond Qwen3.5", key specs, pre-quantized FP8 availability.

### Check 5 — NVIDIA DGX Spark Forum

**Data sources (Discourse JSON — append `.json`):**
- `https://forums.developer.nvidia.com/c/accelerated-computing/dgx-spark-gb10/719.json`
- `https://forums.developer.nvidia.com/c/accelerated-computing/dgx-spark-gb10/dgx-spark-gb10-projects/720.json`
- `https://forums.developer.nvidia.com/c/accelerated-computing/dgx-spark-gb10/dgx-spark-gb10-user-forum/721.json`

Fall back to HTML only on JSON error.

**Agent instructions:**
1. Fetch all three JSON endpoints. Scan topics since baseline `forum_last_checked_date`.
2. Flag posts about: performance improvements, new vLLM builds/images, kernel compilation techniques, driver updates, new model results, SM121/SM120 optimizations, spark-vllm-docker updates.
3. Note posts from known community builders (see Machine Config).
4. Classify: ACTION = new result/technique/image that could improve setup; INFO = worth reading; SKIP = unrelated.

**Return:** post count since last check, ACTION/INFO posts with title, author, date, link, one-line summary.

---

## Console Report Format

```text
## Spark Recon — {DATE}
Overall: {ACTION NEEDED / WORTH WATCHING / NO ACTION}

### Arena: {status}
- Top FP8 Qwen3.5 (single-node): {tok/s} ({name}) — {delta}% vs baseline
- Top overall (single-node): {tok/s} ({name})
{recipe diff if actionable}
{new contenders if any}

### vLLM: {status}
- Latest: {version} — {classification}
{relevant items}
{test plan if HIGH}

### spark-vllm-docker: {status}
{new builds or "No new builds"}

### Qwen Models: {status}
{findings or "No new models beyond Qwen3.5"}

### Forum: {status}
- {N} new posts since {date}
{ACTION/INFO items}

### Cross-Correlated Findings
{items that appeared in multiple checks, or "None"}

### Triggered Alerts
{triggers from Recon Triggers table that matched, or "No trigger matches"}
{For each match: trigger pattern → finding source → action text}

### Recommendations
1. {triggered ACTION items first, then general, or "No action needed"}
```

## LAB_NOTEBOOK Entry

Use the Recon Entry Template from `audit-recon-system.md §6`. Append to `~/dev/personal/spark/LAB_NOTEBOOK.md` using `Edit` tool. Auto-increment entry number.

Skill name field: `spark-recon skill`

Check name fields:
- Check 1: Arena Check
- Check 2: vLLM Release Check
- Check 3: spark-vllm-docker Check
- Check 4: Qwen Model Check
- Check 5: NVIDIA Forum Check

## Baseline Update

Follow **Baseline Update Protocol** from `audit-recon-system.md §7`.

Tracking fields (show diffs, confirm before updating):
- `arena_top_fp8_qwen35_tok_s`, `arena_top_fp8_qwen35_entry`, `arena_top_overall_tok_s`, `arena_top_overall_entry`
- `vllm_last_checked_version`, `svd_last_checked_date`, `forum_last_checked_date`

**Never update the `Current Config` section** — only the user changes that after implementing a recommendation.

## /schedule Integration

Register a recurring recon run:

```bash
/schedule create --name spark-recon-biweekly --cron "0 23 * * 0" --skill spark-recon
```

Recommended: **bi-weekly Sunday 23:00 UTC.** Pairs with spark-audit (Tuesday 02:00 UTC).

```bash
/schedule list
/schedule delete --name spark-recon-biweekly
```

---

## SPARK_BASELINE.md Template

Create in the spark project root if missing:

```markdown
# Spark Performance Baseline

Last updated: {DATE}
Last recon: {DATE}

## Current Config
| Field | Value |
|-------|-------|
| image | vllm-custom:sm121-inject |
| model | Qwen/Qwen3.5-35B-A3B |
| single_request_tok_s | 48.6 |
| c16_aggregate_tok_s | 311.7 |
| vllm_version | v0.17.0rc1 |

## Arena Tracking
| Field | Value |
|-------|-------|
| arena_top_fp8_qwen35_tok_s | 52.32 |
| arena_top_fp8_qwen35_entry | Huihui-Qwen3.5-35B-A3B-abliterated (Artyom) |
| arena_top_overall_tok_s | 70.72 |
| arena_top_overall_entry | Qwen3-Coder-Next-int4-AutoRound |

## Version Tracking
| Field | Value |
|-------|-------|
| vllm_last_checked_version | v0.17.1 |
| qwen_current_model | Qwen/Qwen3.5-35B-A3B |

## spark-vllm-docker Tracking
| Field | Value |
|-------|-------|
| svd_last_checked_date | {DATE} |

## Forum Tracking
| Field | Value |
|-------|-------|
| forum_last_checked_date | {DATE} |

## Recon Triggers
| Source | Pattern | Action | Added |
|--------|---------|--------|-------|
| vllm_release | SM121 OR Blackwell OR GB10 | ACTION: Evaluate vLLM upgrade for SM121 kernel improvements | {DATE} |
| arena | tok_s > baseline + 10% | ACTION: Fetch recipe and compare config differences | {DATE} |
| huggingface | Qwen4 OR Qwen3.5 successor | INFO: New Qwen generation may improve quality or efficiency | {DATE} |

## Watch Items
- {Carry-forward notes from previous recon runs}
- {e.g., "#38126 merged to main 2026-03-27, awaiting release"}
- {e.g., "Test pre-quantized Qwen3.5-35B-A3B-FP8 next config change"}

## Automation Schedule
| Task | Frequency | Recommended Time | Schedule Command |
|------|-----------|-----------------|-----------------|
| Spark Recon | Bi-weekly | Sunday 23:00 UTC | `/schedule create --name spark-recon-biweekly --cron "0 23 * * 0" --skill spark-recon` |
| Spark Audit | Weekly | Tuesday 02:00 UTC | `/schedule create --name spark-audit-weekly --cron "0 2 * * 2" --skill spark-audit` |
```
