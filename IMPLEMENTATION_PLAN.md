# Implementation Plan

**Generated:** 2026-07-16 11:22:06
**Based On:** Architecture Review 2026-07-16 (`arch-review/reports/executive-summary.md`, `arch-review/reports/ultra-plan-analysis.md`, and the 9 domain findings under `arch-review/findings/`) — 1 Critical, 14 High, 37 Medium, 35 Low
**Total Phases:** 8
**Estimated Total Effort:** ~2,600 LOC across ~70 files (incl. docs, CI config, tool code, skill frontmatter)

---

## Executive Summary

This plan remediates the 9-agent architecture review of the claude-marketplace repo. The findings de-duplicate into eight coherent change sets rather than 97 isolated patches: the XXE finding surfaced from three domains resolves in one parser fix; the ungated-distribution finding surfaced from four domains resolves in one branch-protection change. The single Critical (unprotected `main` while installs track it, making every CI gate advisory) leads, because until distribution is gated, every later fix can be bypassed by a direct push and any regression auto-ships to all installs.

Three architecture decisions were made before planning (recorded as ADRs during implementation): (1) **branch-protection-only** distribution safety — require CI status checks and block direct pushes, but not an approving review, because a solo maintainer (bus factor 1) would deadlock on required review (ADR-0007); (2) slide-gen is **formally declared an external-dependency plugin** with an `sg` preflight health-check rather than vendoring the engine in-tree (ADR-0008); (3) the `.env` secrets path is **hardened (chmod 600 + warning) and ADR-0003 is amended** to sanction a local-runtime convenience path, rather than forcing Bitwarden into a distributable tool.

Phases sequence by risk-reduction leverage: governance (1) → exploitable-in-code security (2) → injection-surface reduction (3) → CI gate correctness (4) → external-call robustness (5) → slide-gen integrity (6) → docs/policy/hygiene (7) → test/eval safety net (8). Two large items are explicitly scoped OUT to their own future plan: decomposing the 1,796-line `cli.py` god module and raising visual-explainer's coverage floor to 85%+, and building a comprehensive eval corpus for all 39 skills. Phase 8 does only the highest-leverage test subset.

---

## Plan Overview

The critical path is Phase 1 → (2, 3, 4) → 8. Phase 1 must land first: it converts the existing (genuinely strong) CI suite from advisory to enforced, so every subsequent phase's PR is actually gated. Phases 2 and 3 are the security spine (exploitable code, then capability-grant scoping) and carry the most risk reduction after Phase 1. Phase 4 makes the now-enforced gates correct and complete (a lint blind spot hiding 28 errors, a schema job that never validates data, mutable action tags, a whole-runner-env pip-audit). Phases 5–7 are independent hardening/hygiene tracks. Phase 8 (test/eval) trails because it is the largest and lowest-urgency, and one of its items (raising coverage) depends on the tool code stabilising in Phases 2/8.

Findings sharing a root cause are single work items: XXE (DA-01=SE-02=SEC-02) → item 2.1; ungated distribution (PLAT-001=QA-01=INT-06=RISK-02) → item 1.1; `.env` secrets (SEC-03=DA-06) → item 2.2; SSRF (SEC-04=SE-07=DA-09) → item 2.3; slide-gen facets (SA-001/002/004/005, INT-05, RISK-01, PLAT-013) → Phase 6; mypy inconsistency (SE-04=QA-05=PLAT-006) → item 4.2; stale ruff.toml (SA-007=SE-06=PLAT-009) → item 7.4.

### Phase Summary Table

| Phase | Focus Area | Key Deliverables | Est. Complexity | Dependencies | Execution Mode |
|-------|------------|------------------|-----------------|--------------|----------------|
| 1 | Distribution governance | Branch protection (checks-only), rollback runbook, CODEOWNERS, D19 doc fix, ADR-0007 | S (~6 files, ~200 LOC) | None | Sequential |
| 2 | Tool security hardening (code) | Hardened lxml parser + capped floor, `.env` chmod+warn + ADR-0003 amend, SSRF guard, typed backoff, atomic writes | M (~10 files, ~350 LOC) | Phase 1 | Parallel |
| 3 | Injection-surface reduction | Scoped `Bash` across ~15 skills, fetch/act separation in recon, SSH-sudo boundary documented | M (~18 files, ~250 LOC) | Phase 1 | Parallel |
| 4 | CI gate integrity | Lint per-tool tests (fix 28 errors), mypy blocking, schema-data validation, SHA-pinned actions, scoped pip-audit, de-dup runs | M (~12 files, ~300 LOC) | Phase 1 | Sequential |
| 5 | External-call robustness | curl timeouts + status checks, key→header, unique temp files | S (~4 files, ~150 LOC) | Phase 1 | Parallel |
| 6 | slide-gen integrity | External-dependency declaration + `sg` preflight, homepage/README fix, CHANGELOGs, ADR-0008 | M (~9 files, ~300 LOC) | Phase 1; U1 | Parallel |
| 7 | Docs, egress policy & hygiene | Egress/confidentiality policy, supply-chain docs, help-skill drift, cruft removal | M (~14 files, ~350 LOC) | Phase 1 | Parallel |
| 8 | Test/eval safety net (scoped) | generate_batch decision, fix contradictory skips, eval-mapping CI check, `-n auto`, targeted evals | L (~15 files, ~700 LOC) | Phases 2, 4 | Parallel |

### Execution Hints

| Phase | Model Tier | Context Budget | Notes |
|-------|------------|----------------|-------|
| All (default) | `sonnet` | Standard | Override per-phase below |
| 1 | `sonnet` | Standard | 1.1 branch protection is a `gh api` call + judgment on required-check names |
| 2 | `sonnet` | Extended | Security-sensitive code; 2.1/2.3 warrant care but are single-file |
| 3 | `sonnet` | Extended | Delicate — each rescoped skill must be regression-tested (U2) |
| 8 | `opus` | Extended | 8.1 (generate_batch wiring + memory cap) is judgment-heavy async work |

### Milestones

| Milestone | Phases | Description |
|-----------|--------|-------------|
| Critical + Security (ship first) | 1–3 | Distribution gated; exploitable code paths closed; capability grants scoped. Marketplace is safe to keep auto-distributing. |
| Hardening & Correctness | 4–7 | CI gates correct; external calls resilient; slide-gen honest; docs/policy complete. |
| Full remediation | 1–8 | All in-scope High/Medium findings closed; behavioral safety net seeded. |

<!-- BEGIN PHASES -->

---

## Phase 1: Distribution Governance

**Estimated Complexity:** S (~6 files, ~200 LOC)
**Dependencies:** None
**Execution Mode:** Sequential

### Goals

- Convert the entire existing CI suite from advisory to enforced (close the single Critical finding).
- Give the solo maintainer a time-bounded recovery path for a bad `main`.
- Correct the inaccurate `autoUpdate` documentation.

### Work Items

#### 1.1 Enable branch protection on `main` (checks-only) ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: sonnet**
**Recommendation Ref:** PLAT-001, QA-01, INT-06, RISK-02, INT-11
**Files Affected:**
- `docs/adr/0007-distribution-safety-model.md` (create)
- (GitHub repo settings — via `gh api`, not a repo file)

**Description:**
Enable GitHub branch protection on `main` requiring the existing CI status checks to pass before merge and blocking direct pushes. Per decision D1, require **status checks only — NOT an approving review** (author == reviewer at bus factor 1 would deadlock), and leave `enforce_admins` false so the maintainer retains an escape hatch. Generate ADR-0007 documenting the branch-protection-only model with alternatives (stable/tagged release channel; status quo) and their rejection reasons.

**Tasks:**
1. [ ] Enumerate the exact required check names from a recent green run (`Run Tests (ubuntu-latest)`, `Run Tests (windows-latest)`, the 3 per-tool test jobs, `Validate Plugins`, `Validate Plugins (official CLI)`, `Schema Validation`, `Lint Markdown`, `Dependency Security Audit`, `CodeQL`).
2. [ ] `gh api -X PUT repos/davistroy/claude-marketplace/branches/main/protection` with `required_status_checks.strict=true`, the check contexts, `required_pull_request_reviews=null`, `enforce_admins=false`, `allow_force_pushes=false`, `restrictions=null`.
3. [ ] Write `docs/adr/0007-distribution-safety-model.md` (Status: Accepted) from `references/adr-template.md`.

**Acceptance Criteria:**
- [ ] WHEN `gh api repos/davistroy/claude-marketplace/branches/main/protection` is called THEN it SHALL return HTTP 200 with the required check contexts listed.
- [ ] WHEN a PR has any required check red THEN GitHub SHALL block its merge button.
- [ ] WHEN a direct `git push origin main` is attempted THEN it SHALL be rejected.
- [ ] ADR-0007 exists with Status Accepted and documents the two rejected alternatives.

**Notes:**
Branch-protection settings are API-managed state, fully reversible via `gh api -X DELETE .../protection` (rollback). Do NOT set required reviewers. Confirm the check *names* exactly match what Actions reports (case/spacing sensitive) or the gate silently never satisfies.

#### 1.2 Maintainer incident & rollback runbook ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: sonnet**
**Recommendation Ref:** PLAT-002
**Files Affected:**
- `docs/RUNBOOK.md` (create) or `TROUBLESHOOTING.md` (modify — add "Maintainer: Bad Release Recovery")

**Description:**
Document the maintainer-side P1 procedure absent today: detect a bad `main` → `git revert <merge-sha>` → re-verify → propagation timing (restart-gating + `claude plugin update`) → the user-side version-pin escape hatch (how a consumer freezes on a known-good commit while a fix lands).

**Tasks:**
1. [ ] Write the detect → revert → verify → propagate sequence with exact commands.
2. [ ] Document the user version-pin/freeze escape hatch.
3. [ ] Cross-link from SECURITY.md and TROUBLESHOOTING.md.

**Acceptance Criteria:**
- [ ] WHEN a bad change reaches `main` THEN a non-author following the runbook SHALL be able to revert and confirm propagation without prior context.
- [ ] The runbook states a target RTO and the propagation mechanism.

**Notes:** Pairs with 1.1 — protection reduces bad merges; this handles the ones that slip through.

#### 1.3 CODEOWNERS + soften committed SLAs ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: haiku**
**Recommendation Ref:** PLAT-015, RISK-07
**Files Affected:**
- `.github/CODEOWNERS` (create)
- `SECURITY.md` (modify)

**Description:**
Add a CODEOWNERS file (partial bus-factor mitigation / ownership clarity) and soften SECURITY.md's hard vulnerability-response SLAs (48h ack, 2–4wk fix) to best-effort, since a single responder cannot guarantee them during absence.

**Tasks:**
1. [ ] Create `.github/CODEOWNERS` assigning `* @davistroy`.
2. [ ] Reword SECURITY.md §6 timelines to "best-effort target".

**Acceptance Criteria:**
- [ ] CODEOWNERS present and valid.
- [ ] SECURITY.md no longer commits hard timelines a bus-factor-1 maintainer cannot guarantee.

**Notes:** Do NOT add CODEOWNERS as a *required-review* rule in 1.1 (would deadlock solo merges).

#### 1.4 Correct the D19 autoUpdate documentation ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: haiku**
**Recommendation Ref:** Review correction (intake fact #1)
**Files Affected:**
- `LAB_NOTEBOOK.md` (modify — Decision D19 + Current Baseline)
- `CLAUDE.md` (modify if it repeats the claim)

**Description:**
Decision D19 and related docs assert `autoUpdate: true` in marketplace.json. Verified false — `.metadata` holds only description/marketplace_version/schema_version; auto-propagation is Claude Code's install-side default for GitHub-sourced marketplaces. Correct the wording to describe the actual mechanism.

**Tasks:**
1. [ ] Amend D19 to describe install-side origin/main tracking (not a repo flag), preserving the decision's intent per LAB_NOTEBOOK Rule 4 (mark superseded-by-correction, do not delete).
2. [ ] Grep CLAUDE.md / docs for other `autoUpdate: true` claims and correct.

**Acceptance Criteria:**
- [ ] WHEN a reader consults D19 THEN it SHALL accurately describe install-side tracking, not a marketplace.json flag.
- [ ] No remaining doc asserts `autoUpdate: true` as a repo-declared field.

**Notes:** Doc-accuracy only; the distribution *risk* is unchanged and handled by 1.1.

### Phase 1 Testing Requirements

- [ ] `gh api .../branches/main/protection` returns 200 with required checks after 1.1.
- [ ] A throwaway test PR with a deliberately-red check cannot be merged.
- [ ] markdownlint clean on all modified `.md`.

### Phase 1 Completion Checklist

- [ ] All work items complete
- [ ] Branch protection verified active
- [ ] ADR-0007 accepted
- [ ] No regressions introduced

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Protection active | `gh api repos/davistroy/claude-marketplace/branches/main/protection` | HTTP 200, required_status_checks populated |
| Markdown lint | `npx markdownlint-cli '**/*.md' --ignore node_modules --ignore .git --ignore output --ignore 'tests/fixtures/**'` | Exit code 0 |

<!-- END DOD -->

---

## Phase 2: Tool Security Hardening (Code)

**Estimated Complexity:** M (~10 files, ~350 LOC)
**Dependencies:** Phase 1
**Execution Mode:** Parallel

### Goals

- Close the exploitable-in-code paths: XXE, plaintext-key write, SSRF-to-metadata.
- Make external-API failure handling robust and durable state uncorruptible.

### Work Items

#### 2.1 Harden the BPMN XML parser + cap the lxml floor ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: sonnet**
**Recommendation Ref:** DA-01, SE-02, SEC-02
**Files Affected:**
- `plugins/bpmn-plugin/tools/bpmn2drawio/src/bpmn2drawio/parser.py` (modify)
- `plugins/bpmn-plugin/tools/bpmn2drawio/pyproject.toml` (modify)
- `plugins/bpmn-plugin/tools/bpmn2drawio/tests/` (add XXE regression test)

**Description:**
`parser.py:54,58` use lxml's default parser on attacker-authored BPMN. Build a hardened `etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, dtd_validation=False, huge_tree=False)` once and pass it to `etree.parse` and `etree.fromstring`. Raise the `pyproject.toml` floor from `lxml>=4.9.0` to `lxml>=5.0,<7` (safe-by-default versions).

**Tasks:**
1. [ ] Add a module-level hardened parser factory; thread it into both parse paths.
2. [ ] Add a regression test: a BPMN with `<!ENTITY xxe SYSTEM "file:///etc/hostname">` must NOT read the file (raises/ignores, no host content in output).
3. [ ] Bump lxml floor and re-lock (`requirements-lock.txt`).

**Acceptance Criteria:**
- [ ] WHEN a BPMN file containing an external SYSTEM entity is parsed THEN the parser SHALL NOT resolve it and SHALL NOT emit local-file content into the `.drawio` output.
- [ ] WHEN the existing 585 bpmn2drawio tests run THEN all SHALL pass (branch coverage ≥90%).

**Notes:** BPMN rarely uses DTDs, so disabling DTD loading is low-risk; the 585-test suite guards regressions.

#### 2.2 Harden the `.env` secrets write + amend ADR-0003 ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: sonnet**
**Recommendation Ref:** SEC-03, DA-06
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/api_setup.py` (modify)
- `docs/adr/0003-bitwarden-secrets.md` (modify — add sanctioned local-runtime exception)

**Description:**
Per decision D3: keep the local `.env` convenience path but `os.chmod(path, 0o600)` after writing and print an explicit warning that keys are stored locally unencrypted and Bitwarden is preferred. Amend ADR-0003 to sanction a narrowly-scoped standalone-tool-runtime `.env` exception (currently the tool violates the Bitwarden-only rule outright).

**Tasks:**
1. [ ] In `_create_env_file`, set mode 0600 and emit the warning.
2. [ ] Amend ADR-0003 with the sanctioned exception + rationale.
3. [ ] Update visual-explainer README to reflect the policy.

**Acceptance Criteria:**
- [ ] WHEN `--setup-keys` writes `.env` THEN the file SHALL be mode 0600 and a plaintext-storage warning SHALL be shown.
- [ ] ADR-0003 documents the sanctioned local-runtime exception; the tool no longer silently contradicts policy.

**Notes:** Read path (`os.getenv`) is unchanged; only the write path hardens.

#### 2.3 SSRF guard on arbitrary-URL fetch ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: sonnet**
**Recommendation Ref:** SEC-04, SE-07, DA-09
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/concept_analyzer.py` (modify)
- tests (add SSRF-block test)

**Description:**
`fetch_url`/`fetch_url_content` follow redirects with no destination filtering — a URL can redirect to `169.254.169.254` or an internal service, and the content egresses to Gemini. Resolve the host and block RFC-1918 / link-local / loopback / metadata ranges; disable or bound redirects (re-validate each hop).

**Tasks:**
1. [ ] Add a host-safety check (resolve → reject private/link-local/loopback).
2. [ ] Bound redirects and re-check each hop's target.
3. [ ] Test: a URL resolving/redirecting to a metadata IP is rejected before fetch.

**Acceptance Criteria:**
- [ ] WHEN a fetch target resolves or redirects to a private/link-local/metadata address THEN the fetch SHALL be refused before any request body is retrieved.
- [ ] WHEN a normal public URL is fetched THEN behavior SHALL be unchanged.

**Notes:** Optional allowlist can be added later; block-list of internal ranges is the minimum.

#### 2.4 Typed exception classification for Gemini backoff ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: sonnet**
**Recommendation Ref:** SE-05, INT-10
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/image_generator.py` (modify)

**Description:**
`image_generator.py:278–287` classifies failures by substring-matching `str(e)` (`"429"`, `"rate"`, `"timeout"`, `"safety"`). Switch to typed `google.genai` exceptions / HTTP `.code` so an SDK message reword can't silently degrade a 429 into a generic ERROR and defeat the backoff path.

**Tasks:**
1. [ ] Catch typed google-genai error classes / inspect `.code`; keep the string-match as a last-resort fallback.
2. [ ] Update/extend the rate-limit and timeout classification tests.

**Acceptance Criteria:**
- [ ] WHEN the SDK raises a typed rate-limit/timeout error THEN classification SHALL use the type/`.code`, not message text.
- [ ] Existing image_generator tests pass.

**Notes:** Low-risk; keep the string fallback for SDK versions lacking typed errors.

#### 2.5 Atomic durable writes + full-length cache key ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: sonnet**
**Recommendation Ref:** DA-02, DA-05
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/` (checkpoint + JSON writers, concept cache)

**Description:**
`save_checkpoint` and the metadata/eval/analysis writers write directly to the final path — an interrupted write truncates `checkpoint.json` and breaks resume (costly: paid Gemini generations). Write to a temp file in the same dir and `os.replace()` (atomic); add a `schema_version` key. Use the full-length SHA-256 as the `.cache/` key (currently truncated to 64 bits — a silent wrong-result vector).

**Tasks:**
1. [ ] Wrap durable writes in temp-file + `os.replace`.
2. [ ] Add `schema_version` to checkpoint; handle its absence on load.
3. [ ] Use full hash for cache keys.

**Acceptance Criteria:**
- [ ] WHEN a checkpoint write is interrupted THEN the previous checkpoint SHALL remain intact and loadable.
- [ ] WHEN a checkpoint lacks `schema_version` THEN load SHALL degrade gracefully (no `KeyError`).

**Notes:** `os.replace` is atomic on same-filesystem POSIX + Windows — matches the ubuntu+windows CI matrix.

### Phase 2 Testing Requirements

- [ ] New XXE and SSRF regression tests pass.
- [ ] bpmn2drawio ≥90%, visual-explainer ≥65% branch coverage held.
- [ ] `ruff check` + `ruff format --check` clean on changed tool code.

### Phase 2 Completion Checklist

- [ ] All work items complete
- [ ] All tests passing (both OSes)
- [ ] ADR-0003 amended
- [ ] No coverage regression

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| bpmn tests | `python -m pytest plugins/bpmn-plugin/tools/bpmn2drawio -q --cov=bpmn2drawio --cov-branch --cov-fail-under=90` | Exit 0, ≥90% |
| visual-explainer tests | `python -m pytest plugins/personal-plugin/tools/visual-explainer -q --cov=visual_explainer --cov-branch --cov-fail-under=65` | Exit 0, ≥65% |
| Lint | `ruff check plugins/*/tools/*/src/` | Exit 0 |

<!-- END DOD -->

---

## Phase 3: Injection-Surface Reduction

**Estimated Complexity:** M (~18 files, ~250 LOC)
**Dependencies:** Phase 1
**Execution Mode:** Parallel

### Goals

- Remove the "lethal trifecta" (untrusted content + unscoped `Bash` + egress/SSH) from content-ingesting skills.
- Document the SSH-sudo blast-radius boundary for recon/audit skills.

### Work Items

#### 3.1 Scope `Bash` in content-ingesting skills ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: sonnet**
**Recommendation Ref:** SEC-05, SEC-01
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/skills/{spark-recon,jetson-recon,research-topic,arch-review,analyze-transcript,summarize-feedback,assess-document,visual-explainer,...}` (frontmatter `allowed-tools`)

**Description:**
Replace unscoped `Bash` with `Bash(<cmd>:*)` scopes matching each skill's actual needs, prioritising skills that ingest untrusted web/document/PR content. A content-reading skill should not also hold unrestricted shell (an injected instruction executes with that grant).

**Tasks:**
1. [ ] Inventory every skill/command with unscoped `Bash` (~15).
2. [ ] For each, derive the minimal command scopes from its body and rewrite `allowed-tools`.
3. [ ] Regression-test each rescoped skill on a representative task (U2).

**Acceptance Criteria:**
- [ ] WHEN a rescoped skill runs its normal workflow THEN it SHALL complete without permission-denied regressions.
- [ ] No content-ingesting skill retains unscoped `Bash` unless justified in a Notes comment.
- [ ] `claude plugin validate --strict` passes for all touched plugins.

**Notes:** Delicate — over-scoping breaks skills, under-testing hides breakage. Revert per-skill if a scope proves insufficient. This is the U2 resolution surface.

#### 3.2 Separate untrusted-fetch from local-action in recon/audit skills ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: sonnet**
**Recommendation Ref:** SEC-01
**Depends On:** 3.1
**Files Affected:**
- `plugins/personal-plugin/skills/{spark-recon,jetson-recon,spark-audit,jetson-audit}/SKILL.md`

**Description:**
Restructure recon/audit skills so the "fetch untrusted content" step runs read-only (no `Bash`), separated from any "act locally/remotely" step. Consider `disable-model-invocation: true` on the highest-blast-radius recon skills so injected content cannot auto-trigger them.

**Tasks:**
1. [ ] Split fetch vs act phases in each recon/audit skill body.
2. [ ] Evaluate `disable-model-invocation` for spark-recon/jetson-recon.

**Acceptance Criteria:**
- [ ] WHEN a recon skill fetches third-party content THEN no shell/SSH tool SHALL be active during that fetch step.
- [ ] High-blast-radius recon skills are user-invoke-only where warranted.

**Notes:** Depends on 3.1's scoping being in place.

#### 3.3 Document the SSH-sudo trust boundary (resolve RI-03) ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: sonnet**
**Recommendation Ref:** SEC-01 / RI-03
**Files Affected:**
- `plugins/personal-plugin/skills/{spark-audit,jetson-audit}/SKILL.md` (read/verify)
- `SECURITY.md` (modify — document the boundary)

**Description:**
Confirm whether spark-audit/jetson-audit actually SSH into lab hosts (where the `claude` user has passwordless sudo) with tool grants that an injection could ride. Document the resulting trust boundary in SECURITY.md so the blast radius is explicit.

**Tasks:**
1. [ ] Read the audit skill bodies; confirm/deny SSH-sudo reachability.
2. [ ] Document the boundary and any mitigation in SECURITY.md.

**Acceptance Criteria:**
- [ ] The SSH-sudo blast-radius question (RI-03) is answered in-repo with evidence.
- [ ] SECURITY.md states the trust boundary for fleet recon/audit skills.

**Notes:** Feeds the egress/trust documentation in Phase 7.

### Phase 3 Testing Requirements

- [ ] Each rescoped skill exercised on a representative task with no regression.
- [ ] `claude plugin validate --strict` green for all touched plugins.

### Phase 3 Completion Checklist

- [ ] All work items complete
- [ ] No skill regressions
- [ ] RI-03 resolved and documented

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Plugin validation | `claude plugin validate --strict ./plugins/personal-plugin` | Exit 0 |

<!-- END DOD -->

---

## Phase 4: CI Gate Integrity

**Estimated Complexity:** M (~12 files, ~300 LOC)
**Dependencies:** Phase 1
**Execution Mode:** Sequential

### Goals

- Make the now-enforced gates correct and complete: no lint blind spot, real schema-data validation, blocking types, pinned actions, scoped audit.

### Work Items

#### 4.1 Lint the per-tool tests/ dirs (fix the 28 hidden errors) ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: sonnet**
**Recommendation Ref:** SE-01
**Depends On:** None
**Files Affected:**
- `.github/workflows/validate.yml` (modify globs)
- `plugins/*/tools/*/tests/` (fix 28 ruff errors + format 16 files)

**Description:**
`validate.yml:213,217` lints `plugins/*/tools/*/src/ tests/` — the per-tool `tests/` dirs are unlinted, hiding 28 ruff errors + 16 unformatted files. Fix the errors and formatting FIRST, then extend the globs to include `plugins/*/tools/*/tests/` (order matters — extending first reddens CI).

**Tasks:**
1. [ ] `ruff check --fix` + `ruff format` the per-tool tests.
2. [ ] Manually resolve any non-autofixable errors.
3. [ ] Extend `ruff check` + `ruff format --check` globs to include per-tool tests.

**Acceptance Criteria:**
- [ ] WHEN `ruff check plugins/*/tools/*/tests/` runs THEN it SHALL report 0 errors.
- [ ] validate.yml lints per-tool tests going forward.

**Notes:** Fix-then-extend within one PR.

#### 4.2 Make mypy blocking for all three tools ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: sonnet**
**Recommendation Ref:** SE-04, QA-05, PLAT-006
**Depends On:** None
**Files Affected:**
- `.github/workflows/test.yml` (remove `continue-on-error` at 74, 109)
- tool source (fix surfaced type errors)

**Description:**
Remove `continue-on-error: true` (test.yml:74,109) so mypy blocks for bpmn2drawio and visual-explainer as it already does for feedback-docx. Resolve U4 first (measure error volume) — if large, ratchet with a baseline instead of a big-bang fix.

**Tasks:**
1. [ ] Run `mypy src/` per tool; count errors (U4).
2. [ ] Fix errors, or introduce a ratchet baseline if the volume is high.
3. [ ] Remove `continue-on-error`.

**Acceptance Criteria:**
- [ ] WHEN mypy finds a type error in any of the 3 tools THEN CI SHALL fail.
- [ ] All three tools pass mypy at the chosen strictness.

**Notes:** Gated on U4. Keep `--ignore-missing-imports`; do not jump straight to `--strict`.

#### 4.3 Validate schema *data* + fix schemas/plugin.json ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: sonnet**
**Recommendation Ref:** QA-02, INT-04
**Depends On:** None
**Files Affected:**
- `.github/workflows/test.yml` (schema-validation job)
- `schemas/plugin.json` (modify)
- `scripts/` (add a validator if needed)

**Description:**
The schema-validation job only checks the 4 schemas are well-formed JSON Schema; it never validates plugin/command/questions/answers *data* against them. Wire actual data validation; fix `schemas/plugin.json` (remove the forbidden `tools` property, set `additionalProperties:false`, align the version pattern to `^\d+\.\d+\.\d+$`); wire questions/answers schemas to a consumer or remove them.

**Tasks:**
1. [ ] Fix `schemas/plugin.json` contradictions.
2. [ ] Add a CI step validating each plugin.json + command frontmatter + any questions/answers artifacts against the schemas.
3. [ ] Resolve U6 (surface + fix any existing violations).

**Acceptance Criteria:**
- [ ] WHEN a plugin.json violates `schemas/plugin.json` THEN the schema-validation job SHALL fail.
- [ ] `schemas/plugin.json` no longer contradicts `claude plugin validate --strict`.

**Notes:** The `strict` CLI already catches the `tools` case pre-merge, but the shipped schema must stop misleading contributors.

#### 4.4 Pin GitHub Actions to SHAs; fix dependabot claim; add concurrency/timeout ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: haiku**
**Recommendation Ref:** PLAT-004, SEC-06, PLAT-008
**Depends On:** None
**Files Affected:**
- `.github/workflows/{validate.yml,test.yml}` (modify)
- `.github/dependabot.yml` (fix false SHA-pin comment)

**Description:**
Pin `actions/checkout@v4`, `setup-python@v5`, `setup-node@v4` to full commit SHAs (Dependabot bumps SHAs), making the dependabot.yml "SHA-pinned" comment true. Add a `concurrency:` group (cancel superseded PR runs) and `timeout-minutes` to each job.

**Tasks:**
1. [ ] Replace tag pins with SHA pins (+ `# vX` comment).
2. [ ] Fix the dependabot.yml comment.
3. [ ] Add `concurrency` + `timeout-minutes`.

**Acceptance Criteria:**
- [ ] All third-party actions are SHA-pinned.
- [ ] Superseded PR runs are auto-cancelled; no job can exceed its timeout.

**Notes:** Mechanical; verify each SHA maps to the intended tag.

#### 4.5 Scope pip-audit to tool deps; de-dup redundant runs; root coverage ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: sonnet**
**Recommendation Ref:** PLAT-007, QA-10, PLAT-005, QA-06
**Depends On:** None
**Files Affected:**
- `.github/workflows/{test.yml,validate.yml}` (modify)

**Description:**
Scope `pip-audit` to the tools' locked deps (`--requirement <lock>`) instead of the whole runner env (removes the setuptools-class false-failure recurrence — the Entry-016 workaround is a band-aid). De-duplicate the ~3× root-suite runs and add coverage measurement to root `tests/`.

**Tasks:**
1. [ ] Convert pip-audit to per-lockfile scoping.
2. [ ] Remove the redundant root pytest invocation(s).
3. [ ] Add `--cov` to the root suite with a sensible floor.

**Acceptance Criteria:**
- [ ] WHEN a runner-shipped build tool has a CVE THEN the audit job SHALL NOT fail on it (only tool deps are audited).
- [ ] The root suite runs once per OS with coverage reported.

**Notes:** Undoes the need for the Entry-016 `setuptools` upgrade hack.

### Phase 4 Testing Requirements

- [ ] Injected type error fails CI; malformed plugin.json fails schema job; per-tool tests lint clean.
- [ ] All CI jobs green both OSes after changes.

### Phase 4 Completion Checklist

- [ ] All work items complete
- [ ] CI green both OSes
- [ ] No advisory gate remains where it should block

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Lint (incl. tests) | `ruff check plugins/*/tools/*/src/ plugins/*/tools/*/tests/ tests/` | Exit 0 |
| Types | `mypy plugins/bpmn-plugin/tools/bpmn2drawio/src/ --ignore-missing-imports` | Exit 0 |
| Schema data | `python scripts/validate_schemas_data.py` (new) | Exit 0 |

<!-- END DOD -->

---

## Phase 5: External-Call Robustness

**Estimated Complexity:** S (~4 files, ~150 LOC)
**Dependencies:** Phase 1
**Execution Mode:** Parallel

### Goals

- Make the raw-curl research/brain-entry integrations fail fast and cleanly instead of hanging.

### Work Items

#### 5.1 Add timeouts to every raw-curl external call ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: haiku**
**Recommendation Ref:** INT-01
**Files Affected:**
- `plugins/personal-plugin/references/research-provider-protocols.md` (modify)
- `plugins/personal-plugin/skills/brain-entry/SKILL.md` (modify)

**Description:**
Every `curl` (Anthropic/OpenAI/Gemini research legs + brain-entry POST) lacks `--max-time`/`--connect-timeout`; a hung connection blocks indefinitely and the 30-min poll bound is illusory (it caps poll count, not any single curl). Add `--max-time 60 --connect-timeout 10` (per-provider tunable).

**Tasks:**
1. [ ] Add timeout flags to all curl invocations.
2. [ ] Add `--retry` w/ backoff for idempotent GET polls.

**Acceptance Criteria:**
- [ ] WHEN an external endpoint is unresponsive THEN the curl SHALL abort within its `--max-time` rather than hang.

**Notes:** Pure instruction-file edits.

#### 5.2 Check HTTP status / job ID after submit; honor 429 ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: sonnet**
**Recommendation Ref:** INT-02, INT-07
**Depends On:** 5.1
**Files Affected:**
- `plugins/personal-plugin/references/research-provider-protocols.md` (modify)

**Description:**
Submits never check HTTP status; a failed submit yields an empty job ID and the poll loop burns ~30 min polling a nonexistent job. Check job-ID non-empty (and `error` absent) immediately after submit and fast-fail; treat missing poll `status`/`state` as an error; honor `Retry-After`/429 in the poll loop.

**Tasks:**
1. [ ] Add post-submit success check with `exit 1` on failure.
2. [ ] Treat missing status as an error signal; add 429/Retry-After handling.

**Acceptance Criteria:**
- [ ] WHEN a submit returns 4xx/5xx or an empty job ID THEN the leg SHALL fail fast, not poll for 30 minutes.

**Notes:** Biggest real-world win — turns a 30-min hang into an immediate error.

#### 5.3 Gemini research key → header; unique temp filenames ✅ Completed 2026-07-16
**Status: COMPLETE [2026-07-16]**
**Model Tier: haiku**
**Recommendation Ref:** INT-03, INT-09
**Depends On:** None
**Files Affected:**
- `plugins/personal-plugin/references/research-provider-protocols.md` (modify)

**Description:**
Move the Gemini research key from `?key=$GOOGLE_API_KEY` (leaks to `ps`/history/logs) to the `x-goog-api-key` header. Include the run TIMESTAMP in the fixed `/tmp` response filenames to avoid clobbering across concurrent runs.

**Tasks:**
1. [ ] Switch Gemini legs to `x-goog-api-key` header.
2. [ ] Add TIMESTAMP to temp filenames.

**Acceptance Criteria:**
- [ ] WHEN the Gemini research leg runs THEN the key SHALL NOT appear in the process list or URL.
- [ ] Two concurrent research runs SHALL NOT clobber each other's temp files.

**Notes:** Anthropic/OpenAI legs already use headers correctly.

### Phase 5 Testing Requirements

- [ ] Dry-run a research leg against an unreachable host — fast-fails within timeout.
- [ ] `ps` during a Gemini leg shows no key.

### Phase 5 Completion Checklist

- [ ] All work items complete
- [ ] markdownlint clean
- [ ] No key in process list / URL

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Markdown lint | `npx markdownlint-cli plugins/personal-plugin/references/research-provider-protocols.md plugins/personal-plugin/skills/brain-entry/SKILL.md` | Exit 0 |

<!-- END DOD -->

---

## Phase 6: slide-gen Integrity

**Estimated Complexity:** M (~9 files, ~300 LOC)
**Dependencies:** Phase 1; Unknown U1
**Execution Mode:** Parallel

### Goals

- Make slide-gen honest: either it works on install, or its external dependency is loudly declared and preflight-checked.

### Work Items

#### 6.1 Declare slide-gen an external-dependency plugin + `sg` preflight
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** SA-001
**Depends On:** None
**Files Affected:**
- `plugins/slide-gen/README.md` (modify)
- `plugins/slide-gen/skills/sg-full-workflow/SKILL.md` (add preflight)
- `docs/adr/0008-slide-gen-dependency-model.md` (create)

**Description:**
Per decision D2: formally declare slide-gen an external-dependency plugin (do NOT vendor the engine). Add an `sg` health-check preflight to `sg-full-workflow` (and each entry skill) that fails early with an install pointer if `sg` is missing. Generate ADR-0008 documenting external-dependency vs bundling, with rejection reasons. Resolve U1 (is `slide-generator` public/installable?) — if private, the ADR must state slide-gen is owner-only.

**Tasks:**
1. [ ] Resolve U1 (`gh repo view davistroy/slide-generator`).
2. [ ] Add `sg --version` preflight to the workflow entry points.
3. [ ] Write ADR-0008 (Status: Accepted).

**Acceptance Criteria:**
- [ ] WHEN `sg` is not installed and a slide-gen skill runs THEN it SHALL fail early with a clear install instruction (not `sg: command not found` mid-pipeline).
- [ ] ADR-0008 documents the external-dependency decision.

**Notes:** U1 outcome shapes the README wording (public install vs owner-only).

#### 6.2 Fix homepage + document the external dependency in READMEs
**Status: PENDING**
**Model Tier: haiku**
**Recommendation Ref:** SA-002, INT-05, RISK-01, PLAT-013
**Depends On:** 6.1
**Files Affected:**
- `plugins/slide-gen/.claude-plugin/plugin.json` (homepage)
- `plugins/slide-gen/README.md`, root `README.md` (slide-gen section)

**Description:**
Fix `plugin.json` homepage from `github.com/davistroy/slide-generator` to the marketplace repo. Add a prominent "External Dependency / Prerequisites" section to the slide-gen README and the root README slide-gen section (the dependency is currently buried in individual skill bodies).

**Tasks:**
1. [ ] Correct the homepage URL.
2. [ ] Add Prerequisites sections to both READMEs.

**Acceptance Criteria:**
- [ ] slide-gen `plugin.json` homepage points to claude-marketplace.
- [ ] WHEN a user reads either README THEN the `sg` dependency SHALL be stated before the usage steps.

**Notes:** Also extend the manifest-sync CI check to cover `homepage` (ties to INT-05).

#### 6.3 Add CHANGELOGs; document/consolidate the dual Gemini path
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** SA-005, SA-004
**Depends On:** None
**Files Affected:**
- `plugins/slide-gen/CHANGELOG.md` (create)
- `plugins/bpmn-plugin/CHANGELOG.md` (create)
- `plugins/slide-gen/skills/sg-generate-images/SKILL.md` (cross-reference)

**Description:**
Add per-plugin CHANGELOGs to slide-gen and bpmn-plugin (only personal-plugin has one — the two-tier versioning story is incompletely instrumented). Document the two divergent Gemini image paths (visual-explainer tool vs `sg generate-images`) with a shared-contract note, or reference one from the other.

**Tasks:**
1. [ ] Backfill CHANGELOG.md for slide-gen + bpmn-plugin from git history.
2. [ ] Add a cross-reference note between the two Gemini image paths.

**Acceptance Criteria:**
- [ ] Both plugins have a CHANGELOG traceable through their versions.
- [ ] The two Gemini image paths reference each other / a shared contract note.

**Notes:** CHANGELOG backfill is mechanical from `git log`.

### Phase 6 Testing Requirements

- [ ] Preflight fails cleanly when `sg` absent; passes when present.
- [ ] Manifest-sync check covers homepage.

### Phase 6 Completion Checklist

- [ ] All work items complete
- [ ] ADR-0008 accepted
- [ ] U1 resolved and reflected in docs

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Plugin validation | `claude plugin validate --strict ./plugins/slide-gen` | Exit 0 |
| Manifest sync | `python scripts/check_manifest_sync.py` (extended) | Exit 0 |

<!-- END DOD -->

---

## Phase 7: Governance Docs, Egress Policy & Hygiene

**Estimated Complexity:** M (~14 files, ~350 LOC)
**Dependencies:** Phase 1
**Execution Mode:** Parallel

### Goals

- Close the documentation/policy debt (egress, supply-chain, ADR drift) and remove repo cruft.

### Work Items

#### 7.1 Data-egress / confidentiality policy
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** RISK-04, DA-04, SEC-09
**Files Affected:**
- `SECURITY.md` (modify)

**Description:**
Add an explicit egress/confidentiality policy: data-classification guidance, a "never send to third-party AI APIs" list, and pointers to Anthropic/OpenAI/Google DPAs/terms. This is the highest genuine compliance exposure — a user could feed a confidential client deliverable to `/visual-explainer` (→ Gemini) or `/research-topic` (→ 3 providers) with only a soft caution.

**Tasks:**
1. [ ] Write the data-classification + "never send" policy.
2. [ ] Link provider data-processing terms (resolve U5 on retention/training-use).

**Acceptance Criteria:**
- [ ] SECURITY.md states which data classes must not be sent to third-party AI APIs and links provider DPAs.

**Notes:** Pairs with the trust-boundary doc from 3.3.

#### 7.2 Document the supply-chain control set
**Status: PENDING**
**Model Tier: haiku**
**Recommendation Ref:** RISK-03
**Files Affected:**
- `SECURITY.md` (modify)

**Description:**
SECURITY.md mentions none of the real controls (Dependabot, pip-audit, CodeQL, GitGuardian). Add a "Supply-Chain Controls" section enumerating each scanner, cadence, and enforcement point — the controls exist and are well-evidenced (LAB_NOTEBOOK E012/E013/E016); the gap is documentary.

**Tasks:**
1. [ ] Enumerate each control, cadence, enforcement point.

**Acceptance Criteria:**
- [ ] WHEN an auditor reads SECURITY.md THEN each active supply-chain control SHALL be listed.

**Notes:** Cross-reference the branch-protection gate from Phase 1.

#### 7.3 Resolve the ADR-0004 help-skill drift
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** SA-003
**Files Affected:**
- `docs/adr/0004-plugin-encapsulation.md` OR new per-plugin `help` skills
- `scripts/generate-help.py` (wire into CI or remove)

**Description:**
ADR-0004 (Accepted, non-superseded) mandates a `help` skill per plugin; none exist, and `generate-help.py` targets a nonexistent `help.md`. Either restore per-plugin `help` skills and wire generate-help.py into CI, or amend ADR-0004 to drop the requirement and remove/repurpose the dead script. (Recommend amending — skills-first + native `/help` supersede it.)

**Tasks:**
1. [ ] Decide restore-vs-amend; execute.
2. [ ] Remove or wire up generate-help.py accordingly.

**Acceptance Criteria:**
- [ ] No Accepted ADR states a requirement the codebase does not meet.
- [ ] `generate-help.py` either runs in CI or is removed.

**Notes:** Amending is the lower-effort, skills-first-consistent path.

#### 7.4 Repo hygiene sweep
**Status: PENDING**
**Model Tier: haiku**
**Recommendation Ref:** PLAT-010, RISK-05, SE-08, SA-007, PLAT-009
**Files Affected:**
- root (`GITHUB_ERRORS.md`, `gap-analysis-2026-04-30.md`, `uv.lock`), `docs/archive/GITHUB_ERRORS.md`, `ruff.toml`

**Description:**
`git rm` the tracked cruft (`GITHUB_ERRORS.md` root + `docs/archive/` copy, `gap-analysis-2026-04-30.md`); fix or remove the 52-byte placeholder `uv.lock` (misleading vs the real one under visual-explainer); drop the stale `ruff.toml:35` `research_orchestrator` first-party entry. (`.DS_Store` is already untracked — no action.)

**Tasks:**
1. [ ] Remove the cruft files.
2. [ ] Drop the stale ruff.toml entry.
3. [ ] Remove the markdownlint special-case ignore for the deleted GITHUB_ERRORS.md.

**Acceptance Criteria:**
- [ ] `git ls-files` shows none of the cruft.
- [ ] `ruff.toml` has no dead first-party entry.

**Notes:** Trivial; batch into one commit.

#### 7.5 Add Python 3.10/3.12 to CI matrix; failure sections for 8 skills
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** PLAT-012, SE-10
**Files Affected:**
- `.github/workflows/test.yml` (matrix)
- 8 skill/command files lacking error/failure sections

**Description:**
CI pins Python 3.11 only despite `py310` target + 3.10+ claim. Add 3.10 (and optionally 3.12) to the matrix. Add failure-branch/troubleshooting sections to the 8 skill/command files that lack them (undefined LLM behavior on failure branches).

**Tasks:**
1. [ ] Extend the CI Python matrix.
2. [ ] Add Error Handling sections to the 8 files.

**Acceptance Criteria:**
- [ ] CI runs the tool suites on Python 3.10 and 3.11 (min).
- [ ] The 8 flagged files have an Error Handling section.

**Notes:** Matrix expansion may surface a py310 incompat — fix if so.

### Phase 7 Testing Requirements

- [ ] markdownlint clean; CI matrix green on 3.10 + 3.11.
- [ ] `git ls-files` clean of cruft.

### Phase 7 Completion Checklist

- [ ] All work items complete
- [ ] SECURITY.md updated (egress + supply-chain)
- [ ] No stale config/cruft remains

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Markdown lint | `npx markdownlint-cli '**/*.md' --ignore node_modules --ignore .git --ignore output --ignore 'tests/fixtures/**'` | Exit 0 |
| Cruft gone | `git ls-files \| grep -E 'GITHUB_ERRORS\|gap-analysis-2026'` | No output |

<!-- END DOD -->

---

## Phase 8: Test/Eval Safety Net (Scoped)

**Estimated Complexity:** L (~15 files, ~700 LOC)
**Dependencies:** Phases 2, 4
**Execution Mode:** Parallel

### Goals

- Seed a behavioral safety net on the highest-risk surface and fix inert/contradictory test constructs. (Full cli.py decomposition + comprehensive eval corpus are OUT of scope — separate plan.)

### Work Items

#### 8.1 Resolve the dead `generate_batch` concurrency
**Status: PENDING**
**Model Tier: opus**
**Recommendation Ref:** PERF-01, PERF-05
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/{image_generator.py,cli.py}` (modify)

**Description:**
`generate_batch()` (the `asyncio.gather` path the semaphore governs) is defined but never called; the CLI runs images serially, so `--concurrency` and the semaphore are inert. Per decision: wire the primary path through `generate_batch` (parallelise across images, keep per-image refine serial) with a memory cap (≤3 concurrent 4K buffers per PERF-05), OR remove the `--concurrency` flag + semaphore to stop advertising an inert capability. Choose wiring if the wall-clock win justifies it; otherwise remove.

**Tasks:**
1. [ ] Decide wire-vs-remove (default: wire with memory cap; fall back to remove if risk too high).
2. [ ] Implement + test the chosen path; free buffers promptly if parallelising.

**Acceptance Criteria:**
- [ ] Either `--concurrency` measurably parallelises multi-image runs (with a memory cap), OR the flag/semaphore are removed and no inert knob is advertised.
- [ ] visual-explainer coverage floor (≥65%) held.

**Notes:** Opus — judgment-heavy async + memory-ceiling reasoning.

#### 8.2 Fix contradictory / conditional test skips
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** QA-07, QA-08
**Files Affected:**
- `plugins/personal-plugin/tools/visual-explainer/tests/{test_integration.py,test_image_evaluator.py}`

**Description:**
`test_full_pipeline_success` mocks the APIs yet is `skipif(not ANTHROPIC_API_KEY)`, so the only full-pipeline test never runs in CI. Remove the key gate (it's mocked). Make the resize/eval conditional skips deterministic (fixture that guarantees the branch runs) so a green run actually exercises them.

**Tasks:**
1. [ ] Un-gate the mocked full-pipeline test from ANTHROPIC_API_KEY.
2. [ ] Replace runtime-conditional skips with deterministic fixtures.

**Acceptance Criteria:**
- [ ] WHEN CI runs THEN `test_full_pipeline_success` SHALL execute (not skip).
- [ ] The resize branch is exercised by a deterministic test.

**Notes:** Improves real coverage without changing the floor.

#### 8.3 Eval-mapping CI check + targeted high-risk evals
**Status: PENDING**
**Model Tier: sonnet**
**Recommendation Ref:** QA-03 (subset), SA-006
**Files Affected:**
- `scripts/` (add eval-mapping check), `.github/workflows/validate.yml`
- `evals/` (remove drift; add evals for release-plugin, arch-review, ultra-plan, leak-risk-audit)

**Description:**
Add a CI check that every `evals/*.eval.md` maps to a live skill/command (kills the help/new-command drift, SA-006). Add behavioral evals for the highest-blast-radius skills (release-plugin, arch-review, ultra-plan, leak-risk-audit). Full-corpus coverage of all 39 skills is OUT of scope (separate plan).

**Tasks:**
1. [ ] Remove/repair drifted evals (help, new-command).
2. [ ] Add the eval-mapping CI check.
3. [ ] Author evals for the 4 high-risk skills.

**Acceptance Criteria:**
- [ ] WHEN an eval references a nonexistent skill/command THEN CI SHALL fail.
- [ ] The 4 high-blast-radius skills have evals.

**Notes:** Scoped subset — not the full corpus.

#### 8.4 Add `pytest -n auto` to per-tool CI jobs
**Status: PENDING**
**Model Tier: haiku**
**Recommendation Ref:** PERF-06
**Depends On:** None
**Files Affected:**
- `.github/workflows/test.yml`, per-tool `pyproject.toml` (add pytest-xdist dev dep)

**Description:**
Per-tool jobs run plain `pytest` with branch-coverage tracing, no parallelism; Windows is the slow leg. Add `-n auto` (pytest-xdist) to cut developer-loop latency.

**Tasks:**
1. [ ] Add pytest-xdist to each tool's dev deps + lock.
2. [ ] Add `-n auto` to the per-tool test commands.

**Acceptance Criteria:**
- [ ] Per-tool CI jobs run tests in parallel; suites still pass at the same coverage floors.

**Notes:** Verify coverage aggregation works under xdist.

### Phase 8 Testing Requirements

- [ ] Full-pipeline test runs in CI; eval-mapping check fails on a dangling eval.
- [ ] Coverage floors held under xdist.

### Phase 8 Completion Checklist

- [ ] All work items complete
- [ ] No inert concurrency knob advertised
- [ ] Eval drift removed

### Definition of Done (Runnable)
<!-- BEGIN DOD -->

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| visual-explainer tests | `python -m pytest plugins/personal-plugin/tools/visual-explainer -q --cov=visual_explainer --cov-branch --cov-fail-under=65` | Exit 0, ≥65% |
| Eval mapping | `python scripts/check_eval_mapping.py` (new) | Exit 0 |

<!-- END DOD -->

<!-- END PHASES -->

---

<!-- BEGIN TABLES -->

## Parallel Work Opportunities

| Work Item | Can Run With | Notes |
|-----------|--------------|-------|
| Phase 2 (all items) | Phase 3, 5, 6, 7 | Distinct file surfaces (tool code vs skill frontmatter vs docs vs slide-gen) |
| Phase 3.1 | Phase 3.3 | 3.2 depends on 3.1; 3.3 is independent read/doc |
| Phase 4 items | — | Sequential-ish: 4.1 fix-then-extend; others independent but share workflow files |
| Phase 5 (all) | Phase 2, 3, 6, 7 | Instruction-file edits, disjoint from code |
| Phase 7 items | Phase 2, 3, 5, 6 | Docs/hygiene, disjoint |

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy | Status |
|------|------------|--------|---------------------|--------|
| Required review deadlocks solo maintainer | Med | High | Require checks only, not review; enforce_admins=false | Mitigated |
| Extending ruff glob (4.1) before fixing reddens CI | High | Low | Fix 28 errors + format first, extend glob last, same PR | Mitigated |
| mypy-blocking (4.2) surfaces many errors | Med | Med | Resolve U4 first; ratchet with baseline if large | Mitigated |
| Hardened lxml parser rejects legit BPMN | Low | Med | BPMN rarely uses DTDs; 585-test suite + new XXE test guard | Mitigated |
| Scoping Bash (3.1) breaks legitimate skill actions | Med | Med | Test each rescoped skill (U2); revert per-skill | Mitigated |
| Parallelising images (8.1) breaches memory ceiling | Med | Med | Cap concurrency by memory budget (PERF-05); else remove knob | Open |
| slide-generator repo private → slide-gen owner-only | Med | Med | Resolve U1 first; ADR-0008 states the constraint honestly | Open |

## Unknowns Register

| ID | Unknown | Severity | Affects | Resolution Strategy | Status |
|----|---------|----------|---------|---------------------|--------|
| U1 | Is the `slide-generator` repo public/installable? | High | Phase 6 (6.1) | `gh repo view davistroy/slide-generator` before Phase 6 | Open |
| U2 | Does scoping `Bash` break any skill's real operations? | High | Phase 3 (3.1) | Test each rescoped skill on a representative task | Accepted (conservative union-scoping + 3 documented broad carve-outs + `claude plugin validate --strict` green; residual runtime risk accepted as skills aren't CI-runtime-testable) |
| U3 | Do recon/audit skills SSH with sudo (RI-03)? | Medium | Phase 3 (3.3) | Read spark-audit/jetson-audit bodies | Resolved [2026-07-16] (yes — spark-audit/jetson-audit SSH with passwordless sudo; jetson-recon combines untrusted fetch + SSH) |
| U4 | How many errors does mypy-blocking surface? | Medium | Phase 4 (4.2) | Run `mypy src/` per tool before removing continue-on-error | Resolved [2026-07-16] (54 bpmn + 98 visual-explainer = 152; count-ratchet baselines 57/101 instead of a full cleanup) |
| U5 | Provider retention/training-use terms (RISK-08) | Medium | Phase 7 (7.1) | Check account tiers + provider DPAs | Open |
| U6 | Does enforcing schema-data validation surface existing violations? | Low | Phase 4 (4.3) | Run the new validator over current manifests | Resolved [2026-07-16] (no — current 3 manifests pass; command.json strictness flagged as follow-up) |

## Success Metrics

- [ ] All phases completed
- [ ] All acceptance criteria met
- [ ] The 1 Critical + 14 High findings are closed or explicitly accepted with rationale
- [ ] `main` branch protection active; a red-CI PR cannot merge
- [ ] Security: XXE/SSRF/plaintext-key paths closed; content-ingesting skills no longer hold unscoped `Bash`
- [ ] CI: no advisory gate where it should block; per-tool tests linted; schema data validated
- [ ] slide-gen either works on install or fails preflight with a clear pointer

## Appendix: Recommendation Traceability

| Recommendation | Source | Phase | Work Item |
|----------------|--------|-------|-----------|
| PLAT-001 / QA-01 / INT-06 / RISK-02 / INT-11 | arch-review | 1 | 1.1 |
| PLAT-002 | arch-review | 1 | 1.2 |
| PLAT-015 / RISK-07 | arch-review | 1 | 1.3 |
| autoUpdate doc correction | review synthesis | 1 | 1.4 |
| DA-01 / SE-02 / SEC-02 | arch-review | 2 | 2.1 |
| SEC-03 / DA-06 | arch-review | 2 | 2.2 |
| SEC-04 / SE-07 / DA-09 | arch-review | 2 | 2.3 |
| SE-05 / INT-10 | arch-review | 2 | 2.4 |
| DA-02 / DA-05 | arch-review | 2 | 2.5 |
| SEC-05 / SEC-01 | arch-review | 3 | 3.1, 3.2 |
| SEC-01 / RI-03 | arch-review | 3 | 3.3 |
| SE-01 | arch-review | 4 | 4.1 |
| SE-04 / QA-05 / PLAT-006 | arch-review | 4 | 4.2 |
| QA-02 / INT-04 | arch-review | 4 | 4.3 |
| PLAT-004 / SEC-06 / PLAT-008 | arch-review | 4 | 4.4 |
| PLAT-007 / QA-10 / PLAT-005 / QA-06 | arch-review | 4 | 4.5 |
| INT-01 | arch-review | 5 | 5.1 |
| INT-02 / INT-07 | arch-review | 5 | 5.2 |
| INT-03 / INT-09 | arch-review | 5 | 5.3 |
| SA-001 | arch-review | 6 | 6.1 |
| SA-002 / INT-05 / RISK-01 / PLAT-013 | arch-review | 6 | 6.2 |
| SA-005 / SA-004 | arch-review | 6 | 6.3 |
| RISK-04 / DA-04 / SEC-09 | arch-review | 7 | 7.1 |
| RISK-03 | arch-review | 7 | 7.2 |
| SA-003 | arch-review | 7 | 7.3 |
| PLAT-010 / RISK-05 / SE-08 / SA-007 / PLAT-009 | arch-review | 7 | 7.4 |
| PLAT-012 / SE-10 | arch-review | 7 | 7.5 |
| PERF-01 / PERF-05 | arch-review | 8 | 8.1 |
| QA-07 / QA-08 | arch-review | 8 | 8.2 |
| QA-03 (subset) / SA-006 | arch-review | 8 | 8.3 |
| PERF-06 | arch-review | 8 | 8.4 |

<!-- END TABLES -->

---

*Implementation plan generated by Claude on 2026-07-16 11:22:06*
*Source: /ultra-plan → /create-plan (from arch-review 2026-07-16)*
