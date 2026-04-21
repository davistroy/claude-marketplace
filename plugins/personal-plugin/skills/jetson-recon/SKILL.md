---
name: jetson-recon
description: Use when checking on Jetson Orin Nano inference performance landscape — scans JetPack updates, llama.cpp releases, small model landscape, NVIDIA Jetson forum, and live device health for actionable changes. Run periodically from the jetson project directory.
allowed-tools: Read, Edit, Glob, Grep, Bash, Agent, WebFetch, WebSearch
paths:
  - "JETSON_BASELINE.md"
  - "JETSON_CONFIG.md"
  - "*_CONFIG.md"
---

# Jetson Recon

Periodic intelligence scan of the Jetson Orin Nano Super inference landscape. Five parallel checks, compared against stored baselines, classified by urgency, cross-correlated, results appended to LAB_NOTEBOOK.md.

**This skill is report + recommend only. It never touches the Jetson system.**

Follow the shared execution framework, trigger logic, cross-correlation, classification, LAB_NOTEBOOK entry templates, baseline update protocol, and web research patterns defined in:
`plugins/personal-plugin/references/patterns/audit-recon-system.md`

---

## Loop Guard — Auto-Activation Safety Check

**Run this check before any other step when the skill is triggered automatically via `paths:`.**

1. Read the last 20 lines of `LAB_NOTEBOOK.md` (if it exists).
2. If any line contains `jetson-recon skill` and a timestamp within the last 5 minutes: **stop immediately** — self-triggered re-entry detected. Output: "Loop guard triggered — jetson-recon ran within last 5 minutes. Skipping." and exit.
3. If `--force` is present in `$ARGUMENTS`: skip this check and proceed regardless.
4. Otherwise: proceed normally.

---

## Machine Config

```yaml
machine:
  name: "Jetson Orin Nano Super 8GB"
  baseline_file: "JETSON_BASELINE.md"
  config_file: "JETSON_CONFIG.md"
  project_root: "~/dev/personal/jetson/"
  notebook_file: "LAB_NOTEBOOK.md"

recon_sources:
  check1_source: "NVIDIA JetPack releases + JetsonHacks"
  check2_source: "https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=5"
  check3_source: "HuggingFace (MCP if available) + web search"
  check4_source: "https://forums.developer.nvidia.com/c/autonomous-machines/jetson-embedded-systems/jetson-projects/78.json"
  check5_source: "SSH to claude@jetson.k4jda.net — live health check"

trigger_sources:
  jetpack: "Check 1 (JetPack/Firmware) findings"
  llamacpp_release: "Check 2 (llama.cpp releases) release notes"
  huggingface: "Check 3 (Small Models) search results"
  forum: "Check 4 (Jetson Forum) post titles and summaries"
  health: "Check 5 (Live Health) status readings"

memory_constraint: "~3 GB GGUF at Q4_K_M (8 GB unified — 4B dense model sweet spot; MoE total params, not active)"
inference_port: 8080
ssh_target: "claude@jetson.k4jda.net"
ssh_key: "~/.ssh/id_claude_code"
service_name: "myscript"
thermal_path: "/sys/devices/virtual/thermal/thermal_zone*/temp"
health_thresholds:
  gen_tok_s_warn_pct: 15   # flag if >15% below baseline_gen_tok_s
  rss_warn_pct: 20         # flag if >20% above baseline_rss_mb
  ram_min_mb: 500          # flag if available RAM < 500 MB
  gpu_idle_warn_c: 75      # flag if GPU temp > 75°C at idle
```

---

## Required Files

| File | Location | Purpose |
|------|----------|---------|
| `JETSON_BASELINE.md` | `~/dev/personal/jetson/` | Performance numbers + last-checked dates + watch items |
| `LAB_NOTEBOOK.md` | `~/dev/personal/jetson/` | Append-only results log |
| `JETSON_CONFIG.md` | `~/dev/personal/jetson/` | Hardware/software inventory (read-only reference) |

If `JETSON_BASELINE.md` doesn't exist, create it using the template at the bottom of this skill.

---

## Check-Specific Instructions

Use the Generic Recon Check Structure from the shared reference. Machine-specific details below.

### Check 1 — JetPack / Firmware Updates

**Agent instructions:**
1. `WebSearch` for: `"JetPack" site:developer.nvidia.com jetson release 2026`, `jetsonhacks JetPack 2026`, `JetPack 7 orin nano 2026`.
2. Compare against baseline `jetpack_version`. Check Orin Nano support specifically — many releases skip it.
3. Look for: CUDA version bumps, kernel/cuDNN/TensorRT updates, critical security patches.
4. Classify: HIGH = new JetPack for Orin Nano or CUDA major bump; MEDIUM = announced but not yet available; LOW = no changes.
5. Note upgrade type: full reflash vs OTA.

### Check 2 — llama.cpp Releases

**Agent instructions:**
1. `WebFetch` the releases API. Compare against baseline `llamacpp_version`.
2. Classify keywords: HIGH = `SM87`, `Ampere`, `Jetson`, `Tegra`, `unified memory`, `aarch64`, CUDA graph; MEDIUM = `flash-attn`, `KV cache`, `GGUF`, quant format, `--mlock`, `--parallel`; LOW = other GPU backends.
3. If HIGH: note specific PRs and impact on Qwen3.5-4B Q4_K_M workload (SM87, CUDA 12.6).
4. Check for breaking changes (build flags, new required libs).

### Check 3 — Small Model Landscape

**CONTEXT:** Memory ceiling is ~3 GB GGUF at Q4_K_M. MoE traps: use total/stored parameter count, not active. Do NOT report models already in JETSON_CONFIG.md.

**Agent instructions:**
1. If HuggingFace MCP available: search 1–7B parameters created after `models_last_checked_date`.
2. `WebSearch`: `best small language model 2026`, `best 4B model GGUF`, `small model Jetson edge inference 2026`, successors to current model family.
3. For each new model: parameter count, architecture (dense vs MoE), context length, GGUF quants + sizes, benchmarks vs current model.
4. Check for new embedding models beating Qwen3-Embedding-4B.
5. Flag same-architecture fine-tunes of current model (zero memory cost to try).

### Check 4 — NVIDIA Jetson Developer Forum

**Agent instructions:**
1. `WebSearch`: `site:forums.developer.nvidia.com jetson orin nano llama.cpp 2026`, `site:forums.developer.nvidia.com jetson orin nano inference optimization 2026`, `site:reddit.com/r/LocalLLaMA jetson 2026`.
2. `WebFetch` forum JSON endpoint (see config above).
3. Look for: optimization techniques, community llama.cpp/inference-engine builds, dusty-nv/jetson-containers updates, tok/s reports on Orin Nano 8GB, JetPack/CUDA issue workarounds, TensorRT-LLM updates.
4. Classify: ACTION = new result/technique/tool that could improve setup; INFO = worth reading; SKIP = unrelated.

### Check 5 — Live Jetson Health

**SSH commands** (each separate):
1. `systemctl status myscript`
2. `uptime`
3. `free -h`
4. `cat ~/llm-server/mode.txt`
5. `cd ~/llm-server/llama.cpp && git log --oneline -1`
6. `df -h /`
7. `swapon --show`
8. Inference test: `curl -s http://localhost:8080/v1/chat/completions -H 'Content-Type: application/json' -d '{"model":"qwen3.5-4b","messages":[{"role":"user","content":"Say hello in exactly 5 words"}],"max_tokens":32}'`
9. Thermals: `cat /sys/devices/virtual/thermal/thermal_zone*/temp 2>/dev/null` (divide by 1000 for °C)
10. Slots: `curl -s http://localhost:8080/slots | python3 -c 'import sys,json; s=json.load(sys.stdin); print("Slots:", len(s))'`

Apply thresholds from `health_thresholds` in Machine Config above. Classify: HEALTHY / DEGRADED / DOWN.

---

## /schedule Integration

Register a recurring recon run:

```
/schedule create --name jetson-recon-biweekly --cron "0 23 * * 0" --skill jetson-recon
```

Recommended: **bi-weekly Sunday 23:00 UTC.** Pairs with jetson-audit (Tuesday 02:00 UTC).

```
/schedule list
/schedule delete --name jetson-recon-biweekly
```

---

## JETSON_BASELINE.md Template

Create in the jetson project root if missing:

```markdown
# Jetson Performance Baseline

Last updated: {DATE}
Last recon: {DATE}

## Current Config
| Field | Value |
|-------|-------|
| device | Jetson Orin Nano Super 8GB |
| jetpack_version | 6.2.2 (R36.5.0) |
| cuda_version | 12.6 |
| llamacpp_version | b8766 |
| current_model | Qwen3.5-4B-Q4_K_M |
| baseline_gen_tok_s | 14.0 |
| baseline_pp_tok_s | 166 |
| baseline_rss_mb | 4631 |
| context_size | 32768 |
| gpu_layers | 999 (full offload) |
| threads | 1 |
| parallel_slots | 1 |
| kv_cache_type | q8_0 |
| flash_attn | on |
| mlock | on |

## Version Tracking
| Field | Value |
|-------|-------|
| llamacpp_latest_seen | b8766 |
| jetpack_latest_orin_nano | 6.2.2 |
| jetpack_next_expected | 7.2 (Q2 2026, Orin support) |

## Model Tracking
| Field | Value |
|-------|-------|
| current_model | Qwen3.5-4B-Q4_K_M |
| current_embedding_model | Qwen3-Embedding-4B-Q4_K_M |
| models_last_checked_date | {DATE} |

## Forum Tracking
| Field | Value |
|-------|-------|
| forum_last_checked_date | {DATE} |

## Recon Triggers
| Source | Pattern | Action | Added |
|--------|---------|--------|-------|
| jetpack | JetPack 7.2 AND (Orin Nano OR Orin) | ACTION: Evaluate JetPack 7.2 upgrade (full reflash, wait for community validation) | {DATE} |
| llamacpp_release | SM87 OR Jetson OR Tegra OR unified memory | ACTION: Check release notes for Jetson-specific improvements | {DATE} |
| huggingface | Qwen4 OR Qwen3.5 successor | INFO: New Qwen generation may improve quality at same size | {DATE} |

## Watch Items
- JetPack 7.2 expected Q2 2026 — will bring Ubuntu 24.04, kernel 6.8, CUDA 13.0. Full reflash required.
- {Carry-forward notes from previous recon runs}

## Automation Schedule
| Task | Frequency | Recommended Time | Schedule Command |
|------|-----------|-----------------|-----------------|
| Jetson Recon | Bi-weekly | Sunday 23:00 UTC | `/schedule create --name jetson-recon-biweekly --cron "0 23 * * 0" --skill jetson-recon` |
| Jetson Audit | Weekly | Tuesday 02:00 UTC | `/schedule create --name jetson-audit-weekly --cron "0 2 * * 2" --skill jetson-audit` |
```
