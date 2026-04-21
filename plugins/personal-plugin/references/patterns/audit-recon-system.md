# Audit/Recon System — Shared Framework

Shared five-check framework for machine-specific audit and recon skills. Each skill supplies machine-specific config values via YAML anchors; this file provides the reusable logic, templates, and cross-cutting patterns.

---

## 1. Execution Framework

Both audit and recon skills follow the same 7-phase execution model:

| Phase | Step | Audit | Recon |
|-------|------|-------|-------|
| 1 | Read baseline/config files | `*_BASELINE.md` + `*_CONFIG.md` | `*_BASELINE.md` + LAB_NOTEBOOK tail |
| 2 | Parse triggers (recon) / load baselines (audit) | Load thresholds from baseline | Parse Recon Triggers table |
| 3 | Launch 5 parallel agents/checks | SSH-based checks | Web + SSH agents |
| 4 | Collect results | All 5 checks return | All 5 agents return |
| 5 | Cross-correlate findings | Severity classification | Multi-check correlation + trigger matching |
| 6 | Classify overall status | NEEDS ATTENTION / OPTIMIZATION AVAILABLE / HEALTHY | ACTION NEEDED / WORTH WATCHING / NO ACTION |
| 7 | Report → LAB_NOTEBOOK entry → (recon only) baseline update prompt | Append audit entry | Append recon entry, ask to update tracking values |

**Read direction:** Audit → audit the live system (never modifies it). Recon → report + recommend only (never touches the target system).

---

## 2. Config Hooks — Machine-Specific Values

Each skill defines these anchors. Reference them throughout the check sections.

### Audit Config Schema

```yaml
# Machine-specific config block — supplied by each audit skill
machine:
  name: "{MACHINE_NAME}"            # e.g., "Jetson Orin Nano", "DGX Spark"
  ssh_target: "{SSH_TARGET}"        # e.g., "claude@jetson.k4jda.net"
  ssh_key: "~/.ssh/id_claude_code"
  baseline_file: "{BASELINE_FILE}"  # e.g., "JETSON_BASELINE.md"
  config_file: "{CONFIG_FILE}"      # e.g., "JETSON_CONFIG.md"
  project_root: "{PROJECT_ROOT}"    # e.g., "~/dev/personal/jetson/"
  notebook_file: "LAB_NOTEBOOK.md"

check1_config:
  # Service/container identification — machine-specific
  # Jetson: service via systemctl (myscript), script at ~/llm-server/start.sh
  # Spark: containers via docker inspect (qwen35, qwen3-embed, gliner)
  drift_reference: "{CONFIG_FILE}"  # ground truth for drift detection

check2_config:
  # Optimization flag table — machine-specific (see Check 2 in each skill)

check3_config:
  memory_ceiling: "{MEMORY_CEILING}"  # e.g., "8 GB unified", "121.6 GiB GPU"
  # Memory health thresholds — machine-specific

check4_config:
  # Health endpoints and commands — machine-specific
  inference_port: "{INFERENCE_PORT}"  # e.g., 8080 (Jetson), 8000/8001/8002 (Spark)

check5_config:
  baseline_version_key: "{VERSION_KEY}"  # baseline field tracking the primary version
  # Version comparison targets — machine-specific
```

### Recon Config Schema

```yaml
# Machine-specific config block — supplied by each recon skill
machine:
  name: "{MACHINE_NAME}"
  baseline_file: "{BASELINE_FILE}"
  project_root: "{PROJECT_ROOT}"
  notebook_file: "LAB_NOTEBOOK.md"

recon_sources:
  check1_source: "{PRIMARY_DATA_SOURCE}"   # e.g., NVIDIA JetPack releases, Arena leaderboard
  check2_source: "{SECONDARY_SOURCE}"      # e.g., GitHub releases API URL
  check3_source: "{TERTIARY_SOURCE}"       # e.g., community builds repo
  check4_source: "{MODEL_SOURCE}"          # e.g., HuggingFace + web search
  check5_source: "{FORUM_SOURCE}"          # e.g., Jetson forum, DGX Spark Discourse

trigger_sources:
  # Maps source keys in Recon Triggers table to which check they apply
  # Defined per-skill — see source mapping section in each skill
```

---

## 3. Shared Audit Five-Check Template

Each check follows this generic structure. Machine-specific commands and thresholds are defined in each skill's config block.

### Generic Check Structure

```
### Check N — {NAME}

**Purpose:** {one-line purpose}

**Commands:**
{machine-specific SSH commands}

**Analysis:**
{machine-specific thresholds table}
| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
{rows}

**Return:** {what this check produces — passed to cross-correlation}
```

### Check 1 — Config Drift

**Purpose:** Detect differences between documented config and actual running config.

**Generic analysis pattern:**
1. Extract actual running config (process flags or container inspect output).
2. Compare against documented config file (ground truth).
3. Flag differences by severity:
   - **CRITICAL:** Wrong model path, missing GPU access, wrong port, hang-inducing flag
   - **WARNING:** Flag differences, env var changes, parameter mismatches
   - **INFO:** Cosmetic differences, default values made explicit

**Return:** Drift report with per-item severity classification.

---

### Check 2 — Missing Optimizations

**Purpose:** Compare running config against known best practices for this machine.

**Generic analysis pattern:**
1. Read the optimization flag/setting table from the skill's config block.
2. For each known-good flag: check presence in running config.
3. For each known anti-pattern: check absence in running config.
4. Assign severity per flag table.

**Return:** List of missing optimizations and active anti-patterns, each with severity and expected impact.

---

### Check 3 — Memory Budget

**Purpose:** Verify memory allocation is healthy within the machine's memory constraint.

**Generic memory budget calculation:**
1. Determine total memory ceiling (unified RAM for Jetson; GPU VRAM for Spark).
2. Sum active allocations (model weights + KV cache + runtime + OS overhead).
3. Calculate headroom = ceiling - total.
4. Compare each metric against machine-specific healthy/warning/critical thresholds.

**Memory health thresholds vary by machine** — see each skill's config block. Common axes:
- Available RAM / free GPU memory
- Swap usage
- Per-process allocation vs baseline
- Total allocation vs ceiling

**Return:** Memory budget table, swap/GPU status, headroom, whether allocation is healthy.

---

### Check 4 — System Health

**Purpose:** Check overall system health indicators.

**Generic health axes:**
| Check | Healthy | Warn/Critical |
|-------|---------|---------------|
| Inference endpoint | Responds < 5s | Slow/no response |
| Thermal readings | Machine-specific thresholds | Machine-specific thresholds |
| System uptime | Stable (> 1 day) | < 1 day / service down |
| Disk usage | < 70% | 70–85% / > 85% |
| Error log scan | No relevant errors | GPU/CUDA warnings / OOM kills |

**Inference speed check (when baseline available):**
- Within 15% of baseline: OK
- 15–30% below baseline: WARNING (thermal throttling? memory pressure?)
- > 30% below baseline: CRITICAL

**Return:** Health status per component, inference speed vs baseline, anomalies.

---

### Check 5 — Version Currency

**Purpose:** Compare running versions against latest known-good versions.

**Generic version gap severity:**
| Gap Size | Severity |
|----------|----------|
| Primary component > 1 minor version behind | HIGH |
| Primary component 1 patch behind | MEDIUM |
| Secondary components behind | LOW / INFO |
| Running config doesn't match documented config | WARNING |

**Return:** Version comparison table (running vs latest), upgrade recommendations.

---

## 4. Shared Recon Five-Check Template

### Recon Triggers Framework

Read the `## Recon Triggers` table from the baseline file before launching agents. Pass parsed triggers to each agent.

**Table format:**
```markdown
| Source | Pattern | Action | Added |
|--------|---------|--------|-------|
| {source} | keyword1 AND (keyword2 OR keyword3) | ACTION: what to do | date |
| {source} | version >= threshold | INFO: what it means | date |
```

**Pattern matching rules:**
- `AND` — all keywords must be present (case-insensitive substring match)
- `OR` — any keyword matches
- `>= threshold` — for numeric/version comparisons
- Parentheses — group OR clauses within AND expressions

**Trigger effect on classification:**
- `ACTION:` prefix match → elevate overall classification to at minimum **ACTION NEEDED**
- `INFO:` prefix match → flag finding as **WORTH WATCHING** at minimum
- Triggered matches reported in a dedicated **Triggered Alerts** section before recommendations

**Pass triggers to each agent:** Include parsed trigger table in each agent's prompt so agents can flag matches inline alongside normal findings.

---

### Generic Recon Check Structure

```
### Check N — {NAME}

**Data source:** {URL or source description}

**Agent instructions:**
1. {Fetch/search step}
2. Compare against baseline `{field_name}`.
3. Classify findings:
   | Classification | Criteria |
   |---------------|----------|
   | HIGH/ACTION   | {criteria} |
   | MEDIUM/INFO   | {criteria} |
   | LOW/SKIP      | {criteria} |
4. {Additional analysis steps}

**Return:** {findings summary format}
```

---

## 5. Severity Matrices and Cross-Correlation Logic

### Audit Overall Classification

| Status | Criteria |
|--------|----------|
| **NEEDS ATTENTION** | Any CRITICAL finding, or >= 3 HIGH findings, or service DOWN |
| **OPTIMIZATION AVAILABLE** | Any HIGH finding (no CRITICAL), missing key optimizations |
| **HEALTHY** | No HIGH or CRITICAL findings, config matches best practices |

### Recon Overall Classification

| Status | Criteria |
|--------|----------|
| **ACTION NEEDED** | Any `ACTION:` trigger match, major version release with machine relevance, significantly better config/model available, health DEGRADED/DOWN |
| **WORTH WATCHING** | Any `INFO:` trigger match, minor updates, incremental variants, forum techniques |
| **NO ACTION** | Landscape unchanged from baseline, health HEALTHY |

### Cross-Correlation Logic

After all agents return, look for findings that appear in multiple checks — these carry higher confidence:

**Audit cross-correlation patterns:**
- Version gap (Check 5) + optimization flag (Check 2) + forum fix (if applicable) → correlated HIGH
- Memory issue (Check 3) + inference degradation (Check 4) → correlated root-cause analysis
- Config drift (Check 1) explaining health anomaly (Check 4) → actionable correlation

**Recon cross-correlation patterns:**
- New version in release check + forum posts about that version → higher-confidence signal
- New model in model check + community benchmark results → validated finding
- New container build + improved leaderboard entry → leading indicator for performance gain
- Forum technique aligning with new release features → timing opportunity

**Reporting:** Note correlated findings explicitly in the **Cross-Correlated Findings** section. Single-source findings have lower confidence than multi-source corroborations.

---

## 6. LAB_NOTEBOOK Entry Templates

### Audit Entry Template

```markdown
### Entry {N} -- {Machine} Audit ({YYYY-MM-DD})
**Date:** {YYYY-MM-DD HH:MM} UTC
**Operator:** Claude Code ({skill-name} skill)
**Status:** AUDIT -- no changes made

#### Config Drift: {drift items or "None"}
#### Missing Optimizations: {items or "None"}
#### Memory Budget: {allocation summary}, headroom {X}
#### System Health: {HEALTHY/DEGRADED/DOWN}, thermals {X}C, {X} tok/s
#### Version Currency: {current or behind on N components}
#### Overall: {NEEDS ATTENTION / OPTIMIZATION AVAILABLE / HEALTHY}
#### Recommendations: {list or "No action needed"}
```

### Recon Entry Template

```markdown
### Entry {N} -- {Machine} Recon ({YYYY-MM-DD})
**Date:** {YYYY-MM-DD HH:MM} UTC
**Operator:** Claude Code ({skill-name} skill)
**Status:** RECON -- no changes made

#### {Check 1 Name}: {summary line}
#### {Check 2 Name}: {summary line}
#### {Check 3 Name}: {summary line}
#### {Check 4 Name}: {summary line}
#### {Check 5 Name}: {summary line}
#### Cross-Correlated Findings: {items or "None"}
#### Triggered Alerts: {matches or "No trigger matches"}
#### Overall: {ACTION NEEDED / WORTH WATCHING / NO ACTION}
#### Recommendations: {list or "No action needed -- current config remains optimal"}
```

**Auto-increment entry number:** Read the last `## Entry NNN` or `### Entry NNN` line to determine next N.

---

## 7. Baseline Update Protocol (Recon)

After presenting the report, if any tracking values changed:
1. Show specific changes: `field_name: old_value → new_value`
2. Ask: "Update `{BASELINE_FILE}` with these new observed values?"
3. Update **only on explicit user confirmation**.
4. **Never update the `Current Config` section** — that reflects the user's actual running system. Only the user updates it after implementing a recommendation.
5. Update the `Watch Items` section with carry-forward notes.

---

## 8. Web Research Patterns

### When to Use Which Tool

| Scenario | Tool | Notes |
|----------|------|-------|
| Finding recent releases or announcements | `WebSearch` | Use site: operators for precision |
| Fetching structured API data (GitHub releases, Discourse JSON) | `WebFetch` | Append `.json` to Discourse URLs |
| Reading a page that requires JS rendering | browser MCP (`mcp__claude-in-chrome__*`) | Fall back if unavailable |
| HuggingFace model search | `mcp__claude_ai_Hugging_Face__hub_repo_search` if available, else `WebSearch` | MCP preferred for structured results |
| Fetching a specific known URL | `WebFetch` | Faster than search for known endpoints |

### Discourse Forum JSON Pattern

Discourse forums expose JSON at `{url}.json`. Always try JSON first; fall back to HTML only on error.

```
# Example
https://forums.developer.nvidia.com/c/category/123.json
```

### GitHub Releases API Pattern

```
https://api.github.com/repos/{owner}/{repo}/releases?per_page=5
https://api.github.com/repos/{owner}/{repo}/commits?per_page=10
```

### Search Query Patterns

Scope searches by year to avoid stale results:
```
site:{domain} {topic} {year}
"{product}" {feature} {year}
```
