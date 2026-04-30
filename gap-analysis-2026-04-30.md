# Gap Analysis: `ultra-plan` Skill vs. AI-Native Planning Best Practices (2024–2026)

## Important Caveat on Source Access

The GitHub directory at `https://github.com/davistroy/claude-marketplace/tree/main/plugins/personal-plugin/skills/ultra-plan` was not directly fetchable by my tools (GitHub directory listings and raw blob URLs returned permission/robots errors), and the file is not yet indexed on third-party skill marketplaces (LobeHub/SkillsMP only show your `visual-explainer` skill, not `ultra-plan`).

I therefore based the "current state" reconstruction on:

1. The **public marketplace metadata** for an UltraPlan-branded skill on MCP Market (a sibling/likely-related skill) describing a *"rigorous six-phase automated pipeline … 40 to 70 targeted questions … parallel research agents for codebase analysis, web searching, and library documentation … requirement traceability verification and automated self-review for plan validation … automated generation of AI-executable Technical Plans and Product Requirement Documents (PRDs)."*
2. The **`6missedcalls/ultraplan` open-source skill** (same name, same conceptual lineage), whose SKILL.md is fully public and which appears to share the architectural DNA most "ultra-plan" community skills derive from: read-only mode, `.ultraplan/plan.md` persistent state, parallel Explore agents, iterative interview phase, file-path-grounded plan output, and a `references/anti-patterns.md`.
3. The structure of your sibling skill (`visual-explainer`) and the marketplace conventions of `davistroy/claude-marketplace` (Bitwarden-based `/unlock`, `personal-plugin`, BPMN plugin, etc.).

**If your `ultra-plan` differs materially from this reconstructed picture (e.g., different phase count, different artifacts), treat the gap analysis as directional rather than line-item — the recommendations below are framework-level and should remain valid even if specifics differ.** Before the SKILL.md rewrite, paste the actual current SKILL.md into the next session so the rewrite can be precise.

---

## TL;DR

- **Three biggest gaps**: (1) no explicit **constitution / project-rules layer** (Spec Kit's killer feature, also adopted by BMAD/Kiro) that gates plan acceptance; (2) **no formal verification harness or Definition-of-Done contract** linking spec → tasks → tests → acceptance evidence; (3) **planning is treated as a one-shot artifact** rather than a **living spec** with bidirectional drift detection (Kiro's central thesis).
- **Three biggest strengths to preserve**: (1) heavy upfront discovery (40–70 questions) is *more rigorous* than Spec Kit/BMAD defaults and pays off for solo builders; (2) parallel codebase Explore agents + file-path-grounded plans match Anthropic's own internal "Explore → Plan" pattern; (3) PRD + Technical Plan dual output is the right shape for Claude Code's plan-mode handoff to implementation.
- **Top-priority improvements**: add a `constitution.md`/non-negotiables layer, add a **risk + unknowns register**, switch from monolithic `plan.md` to a **decomposed spec/plan/tasks triad** (Spec Kit/Kiro pattern), bake in **context-budget and model-tier directives**, and add an **explicit verification phase** with binary pass/fail acceptance criteria written in EARS-style notation.

---

## 1. Reconstructed Snapshot of `ultra-plan` (Current State)

Based on the marketplace description and lineage, the current skill appears to do the following:

| Dimension | Current behavior (reconstructed) |
|---|---|
| **Trigger** | Invoked by user keyword ("ultra-plan" / "deep plan") or model-invoked when a complex, multi-file task is described. |
| **Mode** | Read-only / planning mode (no edits except to plan artifacts). |
| **Discovery** | Comprehensive interview: 40–70 targeted questions covering requirements, edge cases, non-functional needs, technical preferences. |
| **Research** | Parallel agents: (a) codebase Explore (Glob/Grep/Read), (b) web research, (c) library/dependency documentation lookup. |
| **Outputs** | A **PRD** (product-side intent + acceptance) + a **Technical Plan** (architecture, files, sequence, verification step). Likely persisted under `.ultraplan/` or `docs/plans/`. |
| **Validation** | Requirement-traceability check + automated self-review pass before presenting plan to user. |
| **Phase count** | Six phases (likely: Intake → Interview → Parallel Research → PRD → Technical Plan → Self-Review/Traceability). |
| **Anti-patterns** | Explicit guardrails likely include: don't claim tests pass without running them; file paths mandatory; recommend one approach (not a menu); reuse before create; ask before assume. |
| **Artifacts** | SKILL.md, references/ (probably planning-patterns.md, anti-patterns.md), possibly a companion CLAUDE.md or templates. |
| **Integration** | Operates inside a Claude Code plugin (`personal-plugin`) and likely composes with other plugin skills (BPMN, doc review, etc.). Unclear whether it integrates with **Plan Mode**, **sub-agents** (`Agent` tool with subagent_type), **hooks**, or **MCP** servers. |

**Strengths inherent in this design:**
- Discovery rigor (40–70 questions) far exceeds Spec Kit's `/speckit.specify` (which usually asks 5–10 clarifying questions) and BMAD's Analyst phase. For *solo builds where the user is also the PM*, this front-loads the right work.
- Dual-artifact (PRD + Technical Plan) output respects the "what vs. how" boundary that Spec Kit makes a non-negotiable principle.
- Parallel research + file-path grounding matches the empirically validated "Explore → Plan → Implement → Commit" loop Anthropic publishes as the Claude Code 4-phase workflow.
- Self-review/traceability gate is more than what stock Plan Mode provides.

---

## 2. Synthesis of AI-Native Best Practices (2024–2026)

This is the canon I'm comparing against. I've grouped findings by framework and by cross-cutting practice.

### 2.1 GitHub Spec Kit (the de facto SDD reference)

**Phased workflow (gated):** Constitution → Specify → Plan → Tasks → Implement, with **explicit checkpoints** between each. The user verifies before advancement.

Key artifacts: `constitution.md` (non-negotiable principles, set once via `/speckit.constitution`), `spec.md`, `plan.md`, `tasks.md` (strict checklist format parseable by scripts).

Key principles worth stealing:
- **Specifications are the primary artifact; code is the build output.** This inverts traditional development.
- **Constitution gates** (templates have a `Phase -1: Pre-Implementation Gates` section that must pass each constitutional article or document a justified exception in a "Complexity Tracking" section).
- **Test-first is non-negotiable**: tests written before any implementation, validated, confirmed failing (Red phase), then implementation begins.
- **Branching for exploration**: same `spec.md` → multiple `plan.md` variants on parallel branches to explore different optimization targets.
- **Strict tasks.md format** so scripts can parse it deterministically.
- **Bidirectional feedback**: production reality flows back into spec evolution.

### 2.2 Amazon Kiro (spec-driven IDE)

**Three-phase spec workflow per feature:** Requirements → Design → Tasks. Two flavors: Feature spec or Bugfix spec.

Distinctive elements:
- **EARS notation** for acceptance criteria: `WHEN [event] THEN [system] SHALL [action]` — testable, unambiguous, easy for agents to parse.
- **Steering files** (project-wide guidance) similar to constitution.md but persistent and contextually loaded.
- **Hooks** — event-driven automation (file save, file create, etc.) that triggers agent actions: regenerate tests, update docs, run design compliance checks via Figma MCP, etc.
- **Living specs**: specs stay in sync with the codebase; Kiro can update spec from code changes or refresh tasks from updated specs. This solves the "documentation drift" problem head-on.
- Explicit Vibe Mode vs. Spec Mode distinction — the user picks the level of rigor.

### 2.3 BMAD-METHOD v6

**Two macro phases:** Agentic Planning → Context-Engineered Development.

Distinctive elements:
- **Specialized agent personas** (Analyst, PM, Architect, PO, SM, Dev, QA, Orchestrator). Each is a Markdown/YAML file defining persona, commands, dependencies. Even for solo work this is useful: it lets the *same* model adopt different lenses sequentially without context bleed.
- **Scale-Adaptive planning** — Level 0–4 complexity classification adjusts planning depth (a one-line bug fix gets a one-paragraph plan; an enterprise build gets the full deck). This is a brilliant pattern most planning skills ignore.
- **Just-in-time documentation** — generated as needed, not upfront waterfall.
- **Living, versioned planning artifacts** in Git.
- v6 explicitly adds **Skills Architecture, Sub-Agent inclusion, and Dev Loop Automation**.

### 2.4 Anthropic's Own Guidance (Claude Code, Context Engineering, Long-Running Agents)

The canonical Anthropic patterns (from `code.claude.com/docs`, the Engineering Blog, and the Cookbook):

- **The 4-phase agentic loop**: Explore → Plan → Implement → Commit. Plan and Explore are *the cheapest in tokens, most valuable in outcome*.
- **Plan Mode (`Shift+Tab` or `--permission-mode plan`)** is read-only by design and uses `AskUserQuestion` for clarifications — your skill should *invoke* it, not duplicate it.
- **CLAUDE.md** is for *durable project facts* (build commands, conventions, gotchas). Skills are for *processes* (how to do specific tasks).
- **Skill structure**: YAML frontmatter (`name`, `description`) + markdown body, with progressive disclosure via `references/` and `scripts/` subdirectories. Description must clearly state *when* to invoke (this is the trigger signal).
- **Context engineering primitives**: compaction, tool-result clearing, and external memory (the `/memories` tool or filesystem). "Find the smallest set of high-signal tokens that maximize the likelihood of your desired outcome." Context rot is real even before hard limits.
- **Long-running harness pattern** (from the Anthropic post on harnesses): an *initializer* agent writes a comprehensive feature-requirements file with hundreds of features marked failing → workers implement and flip to passing. This is exactly the "verification harness" pattern your skill is missing.
- **Sub-agents** are the right tool when you need a *fresh context* for a focused subtask (Explore, Plan, Verify). Skill frontmatter `context: fork` runs a skill in an isolated subagent context.
- **Hooks** (PreToolUse, PostToolUse, Stop, SessionStart) are the integration point for enforcement (e.g., a Stop hook that re-runs the verification harness; a PostToolUse hook that re-formats code or blocks edits outside scope).
- **Ultraplan (the Anthropic feature, distinct from your skill)** is now Anthropic's own cloud planning surface — your skill name overlaps and you may want to rename or namespace it (`ultra-plan` vs. Anthropic's `/ultraplan`) to avoid user confusion as the platform feature matures.
- **Ultrathink trigger**: include "ultrathink" in skill content to enable extended thinking for the planning phase.

### 2.5 Practitioner Patterns (Hashimoto, Ronacher, Willison, Huntley, Karunaratne)

Common threads:
- **Separate planning from execution** as a hard discipline, not a suggestion (Hashimoto, Karunaratne).
- **Harness engineering**: every agent failure becomes a permanent test/lint rule the agent can self-check against (Hashimoto). This compounds over time.
- **Priming the agent**: have it read additional context upfront before any task (Karunaratne).
- **The plan file IS the persistent state** — write to disk incrementally, never hold state only in conversation (Manus pattern, also `6missedcalls/ultraplan`, also Anthropic's "effective harnesses" post).
- **Test-time backpressure** beats prompt-time discipline (Huntley/Ralph Wiggum). Tests, typecheck, lint, build must reject invalid work.
- **Acceptance-driven tests** — acceptance criteria → tests during planning, not after.
- **Multi-agent verification** > single-agent self-review (Anthropic's own multi-agent research system; Qt's parallel-reviewer skill).
- **Throwaway code as a tool** — Ronacher's pattern of letting agents write throwaway scripts to introspect state.
- **Logging-as-context** — Ronacher: the agent reads its own logs to recover and verify; Mitchell: design systems for agent-readable diagnostics.

### 2.6 Open standards & ecosystem
- **AGENTS.md** is the emerging cross-tool standard for project-level agent instructions (used by Codex, Cursor, Aider, Factory, etc.). Claude Code can be configured to load it. For a personal-plugin skill, supporting AGENTS.md in addition to CLAUDE.md is now table stakes.
- **EARS-style acceptance criteria** is becoming the lingua franca because it parses cleanly into test stubs.

---

## 3. Side-by-Side Comparison

| Dimension | `ultra-plan` (current) | Spec Kit | Kiro | BMAD v6 | Anthropic Native | Recommendation |
|---|---|---|---|---|---|---|
| Constitution / non-negotiable principles layer | ❌ Implicit only | ✅ `constitution.md` + Phase -1 gates | ✅ Steering files | ✅ PO/Architect persona enforces | Partial (CLAUDE.md) | **ADD** |
| Specs as primary artifact (vs. code) | ⚠️ PRD exists but unclear if living | ✅ Core thesis | ✅ Core thesis, sync with code | ✅ Living docs in Git | Partial | **STRENGTHEN** |
| Phased gates between Spec / Plan / Tasks | ⚠️ Six phases internal, but single output | ✅ 4 hard gates | ✅ 3-phase | ✅ 4-phase | ✅ 4-phase loop | **ALIGN** |
| Discovery interview rigor | ✅ 40–70 questions (best in class) | ⚠️ 5–10 clarifying questions | ⚠️ Free-form chat | ✅ Multi-agent interview | Plan Mode AskUserQuestion | **PRESERVE** |
| Acceptance criteria format | ❓ Likely freeform | Loose | ✅ EARS notation | ✅ Story acceptance | None enforced | **ADOPT EARS** |
| Task decomposition format | ❓ Likely embedded in plan | ✅ Strict `tasks.md` checklist | ✅ Trackable tasks | ✅ Story breakdown | TodoWrite tool | **EXTRACT TASKS** |
| Risk / unknowns register | ❌ Not visible | Partial (Complexity Tracking) | ❌ | Partial | ❌ | **ADD** |
| Test-first discipline | ❓ Probably mentioned | ✅ Non-negotiable Red phase | ✅ Tests in tasks | ✅ QA agent | Recommended | **ENFORCE** |
| Verification harness (running tests as gate) | ⚠️ Self-review only | Implicit | ✅ Hooks | ✅ Dev loop | ✅ Initializer pattern | **ADD** |
| Context-budget directives | ❌ Not visible | ❌ | ❌ | Partial | ✅ Engineering blog | **ADD** |
| Model-tier directives (Opus for plan, Sonnet for code) | ❓ | ❌ | ✅ Auto-routing | Partial | Recommended | **ADD** |
| Sub-agent integration | ⚠️ "parallel research agents" | ❌ | ❌ | ✅ persona-as-subagent | ✅ first-class | **FORMALIZE** |
| Hooks integration | ❌ | ❌ | ✅ central feature | ⚠️ in v6 | ✅ first-class | **OPTIONAL hook recipes** |
| MCP integration | ❓ | Optional | ✅ central | ⚠️ | ✅ first-class | **DOCUMENT** |
| Living spec / drift detection | ❌ | Manual | ✅ central | ✅ versioned | ❌ | **ADD** |
| Branching for exploration (parallel plans) | ❌ | ✅ Creative Exploration phase | ❌ | ❌ | Manual | **OPTIONAL** |
| Anti-patterns / failure-mode catalog | ✅ `anti-patterns.md` | Implicit | ❌ | Implicit | Scattered | **PRESERVE & EXPAND** |
| Scale-adaptive depth (Level 0–4) | ⚠️ "auto-scales" mentioned | ❌ | ❌ | ✅ explicit Levels 0–4 | ❌ | **MAKE EXPLICIT** |
| Cross-tool portability (AGENTS.md) | ❓ | ❌ | ❌ | ⚠️ | Optional | **ADD AGENTS.md compatibility** |

---

## 4. Prioritized Recommendations

### 4.1 Critical Gaps (significant missing capability — fix first)

**C1. Add an explicit Constitution / Project-Rules phase as Phase 0.**

- **Why**: Spec Kit, BMAD, and Kiro have all converged on this. It's the single most impactful pattern for AI-native planning because it gives the agent a stable, gated reference frame *before* the discovery interview begins. Without it, the 40–70 questions can spawn a plan that violates project-wide constraints (test policy, deployment shape, security guardrails) the user hasn't stated explicitly.
- **What to add**: A Phase 0 that either (a) reads an existing `./constitution.md` or `.specify/memory/constitution.md`, or (b) generates one from a 6–10 question interview the *first time* the skill runs in a repo. Articles should be terse — Spec Kit's default uses 9 articles; for solo builds, 5–7 is enough.
- **Concrete implementation sketch**:

```markdown
# Phase 0: Constitution Check
- IF `constitution.md` exists → read and bind every subsequent decision to it
- ELSE run a 7-question setup interview:
  1. Test policy (TDD-required, post-hoc tests OK, prototype-only, etc.)
  2. Deployment target (homelab, Vercel, Modal, local-only)
  3. Stack lock-in (FastAPI, Next.js, etc. — the user's defaults)
  4. Security non-negotiables (Bitwarden /unlock pattern, no .env files, etc.)
  5. Observability minimum (structured logs, tracing yes/no)
  6. Data sovereignty (homelab vs. cloud — relevant for LLM workloads)
  7. Definition-of-Done baseline (lint+typecheck+tests passing? coverage threshold?)
- Add a "Pre-Plan Gates" checklist at the top of every generated plan:
  - [ ] Plan complies with Article 1 (Test policy)
  - [ ] Plan complies with Article 2 (Deployment)
  - ... or document justified exception in §Complexity Tracking
```

**C2. Restructure the single PRD+Plan output into a Spec / Plan / Tasks triad with hard gates.**

- **Why**: A monolithic plan blob is hard to review, hard to update, and impossible for downstream skills/sub-agents to consume cleanly. Spec Kit's separation matches the natural cognitive boundaries: *what* (spec), *how* (plan), *do* (tasks). Each becomes independently re-generatable when upstream changes.
- **What to add**: Three persistent files per feature, e.g., `.ultraplan/<slug>/spec.md`, `plan.md`, `tasks.md`. Use Kiro's EARS notation for acceptance criteria in `spec.md`. Use Spec Kit's strict checklist format in `tasks.md` so a downstream `/implement` or sub-agent can parse it.
- **Concrete implementation sketch**:

```markdown
# spec.md — uses EARS notation
## Requirement R1: User can upload audio file
### Acceptance Criteria
1. WHEN user drags a file into the upload zone THEN the system SHALL validate
   format (mp3, wav, flac) and reject others with inline error.
2. WHEN file size > 100MB THEN the system SHALL chunk-upload via S3 multipart.
...

# plan.md — architecture & file-level changes
## Component: Upload Service
- File: src/services/upload.py:NEW
- Reuses: src/utils/s3.py:upload_chunk (line 47)
- Implements: R1.1, R1.2

# tasks.md — strict, parseable, dependency-ordered
- [ ] T1 [R1.1] Add format validator → src/services/upload.py
- [ ] T2 [R1.1] Tests for validator → tests/test_upload.py (RED first)
- [ ] T3 [R1.2] Chunk upload helper → src/utils/s3.py:line 80 add chunk_upload
- [ ] T4 [R1.2] Integration test → tests/integration/test_upload_chunk.py
```

Each task ID maps back to a requirement ID; this *is* requirements traceability done right for AI agents.

**C3. Add a Verification Harness phase and a Definition-of-Done contract.**

- **Why**: Anthropic's "Effective harnesses for long-running agents" post and Hashimoto's "every mistake becomes a harness improvement" advice both converge on this: AI-generated code that *looks* correct but isn't is the #1 failure mode. A self-review pass (your current Phase 6) is necessary but not sufficient — you need *runnable* gates.
- **What to add**: A Phase that, before the plan is "done," (a) generates the failing tests for each acceptance criterion, (b) writes the runnable verification command into the plan, (c) defines a binary DoD checklist that downstream Implement runs *must* satisfy.
- **Concrete implementation**:

```markdown
## Definition of Done (binary, runnable)
- [ ] All tests in tasks.md test files pass: `pytest tests/ -v`
- [ ] Type-check clean: `mypy src/`
- [ ] Lint clean: `ruff check src/`
- [ ] Coverage on changed files ≥ 80%: `pytest --cov=src/services/upload`
- [ ] No new TODOs, no placeholder strings ("TBD", "implement later")
- [ ] All EARS acceptance criteria mapped to a passing test (traceability matrix below)
- [ ] Architectural compliance: no imports across boundary X→Y (verified by `scripts/check_imports.py`)

## Traceability Matrix
| Req ID | Test File | Test Name | Status |
|--------|-----------|-----------|--------|
| R1.1   | test_upload.py | test_format_validation_rejects_pdf | ❌ (write first) |
```

This is the harness pattern from Anthropic's blog applied to your skill's output.

### 4.2 High-Value Enhancements (would meaningfully improve outcomes)

**H1. Add a Risk & Unknowns Register as a first-class plan section.**

- **Why**: Spec Kit only handles this implicitly via "Complexity Tracking." For Claude Code workflows, unknowns drive context cost — every unknown that surfaces mid-implementation either causes a re-plan or, worse, an unsupervised "best-guess" by the agent.
- **What to add**:

```markdown
## Risks & Unknowns
| ID | Risk/Unknown | Likelihood | Impact | Mitigation/Resolution Strategy | Owner |
|----|--------------|-----------|--------|-------------------------------|-------|
| U1 | DGX Spark vLLM throughput unknown for batch=8 | High | Medium | Spike test before T7; if <X tok/s, switch to TGI | Implement T0 |
| R1 | Bitwarden CLI rate limits during /unlock | Medium | Low | Cache for session via env vars | Already in CLAUDE.md |
```

Make resolving Severity ≥ High items a Pre-Plan Gate.

**H2. Embed context-budget and model-tier directives in the plan.**

- **Why**: Anthropic's context-engineering canon. For solo Claude Code users, *which model handles which phase* is a real cost lever (Opus for planning, Sonnet for implementation, Haiku for triage). Your skill output should declare this explicitly so downstream `/implement` invocations honor it.
- **What to add** — a section in plan.md:

```markdown
## Execution Hints (for downstream skills/sub-agents)
- Suggested model tier per phase: Opus 4.5 (planning, this file) → Sonnet for implementation → Haiku for routine refactors
- Context budget: tasks decomposed for ≤30k tokens per Implement subagent invocation
- Subagent assignment: T1–T4 in one Implement subagent (cohesive); T5 separate (independent module)
- "ultrathink" enabled for: T7 (architectural decision)
- Hook hint: PostToolUse should run `ruff check` after every Edit on src/**/*.py
```

This turns your plan into a directive for the next agent in the pipeline, not just a doc.

**H3. Make scale-adaptivity explicit (BMAD's Levels 0–4 pattern).**

- **Why**: Your current "auto-scales to complexity" is correct in spirit but invisible — both the user and the agent benefit from naming the level. BMAD's Levels 0–4 are well-tested.
- **What to add**: A first-question gate that classifies the work, with templates per level:
  - **L0 (typo/one-liner)**: Skip discovery, single-task plan, no spec.
  - **L1 (single-file feature)**: Compressed spec (3 EARS criteria max), no separate tasks.md.
  - **L2 (multi-file feature)**: Full triad, single repo.
  - **L3 (cross-cutting refactor or new subsystem)**: Full triad + ADR.
  - **L4 (greenfield project / multi-repo)**: Full triad + ADR + parallel-branch creative exploration (Spec Kit pattern).

**H4. Add an Architecture Decision Record (ADR) trigger for L3+.**

- **Why**: Once the plan touches multi-component or cross-cutting concerns, the *why* of architectural choices needs to outlive the plan. ADRs are the standard. Generating them at plan time (not post-hoc) is the AI-native twist (Adolfi.dev, Archgate, AgenticAKM paper all converge on this).
- **What to add**:

```markdown
## ADRs to Generate (L3+ only)
- ADR-NNNN: Choice of vLLM vs. TGI for local LLM serving
  - Status: Proposed
  - Context: ...
  - Decision: vLLM
  - Consequences: ...
  - Alternatives Considered: TGI, llama.cpp
```

Drop them in `docs/adr/`. Have the implementation phase update Status to Accepted on merge.

**H5. Living-spec / drift detection (Kiro's central pattern).**

- **Why**: Specs become stale faster than code; once stale, they actively mislead the agent. Kiro's bidirectional sync is the strongest answer in the field.
- **What to add**: A second skill invocation mode `ultra-plan --refresh` that diffs `spec.md` against current code (using a sub-agent) and produces a drift report with proposed spec updates or a "spec is still accurate" attestation. Pair with a hook recipe:

```bash
# Optional Stop hook
# After significant edits, suggest running /ultra-plan --refresh
```

**H6. Adopt explicit AskUserQuestion patterns and lean on Plan Mode under the hood.**

- **Why**: Don't reinvent. Anthropic's Plan Mode + `AskUserQuestion` are first-class. Your skill should *invoke* Plan Mode for the read-only enforcement (saves you from re-implementing the guardrail) and *batch* clarifying questions via `AskUserQuestion` rather than free-form Q&A.
- **What to add** — in SKILL.md guidance:

```markdown
- Enter Plan Mode for the duration of phases 1–6 (read-only enforcement is free)
- Use AskUserQuestion to batch 5–8 questions per round; never ask one at a time
- After each round, write findings to spec.md before asking the next round
- Cap at 4 rounds × ~15 questions = ~60 questions (matches your 40–70 target)
```

**H7. Formalize the parallel research agents as named sub-agents with frontmatter `context: fork`.**

- **Why**: "Parallel research agents" is currently descriptive; it should be mechanical. Anthropic's skills system supports `context: fork` to run a skill's body in an isolated subagent — this is exactly the right primitive.
- **What to add**: Define three sub-skills (or sub-skill stubs the main skill invokes):
  - `ultra-plan-explore-codebase` (forked, Read/Glob/Grep tools only)
  - `ultra-plan-research-libraries` (forked, WebSearch/WebFetch + Context7 MCP)
  - `ultra-plan-research-domain` (forked, WebSearch only)

Each returns a structured summary back into the main planning context. This *both* improves quality and reduces context-rot in the main session.

### 4.3 Nice-to-Haves (polish, quality of life)

**N1. Add an `AGENTS.md` companion output.** When the plan is approved, generate or update `AGENTS.md` so other agents (Codex, Cursor) on the same repo see consistent guidance. Cross-tool portability matters even for solo users who switch agents.

**N2. Anti-pattern catalog expansion**, with concrete examples and detection heuristics. Your current `anti-patterns.md` should grow to cover: "false completion claims," "fabricated file paths," "scope creep mid-implementation," "skipped acceptance criteria," "TBD/placeholder pollution," "ignoring constitution," "model laziness on long tasks," "premature mocking of internal code." Each with a one-line mitigation.

**N3. Cost-budget annotations.** Optional per-task cost estimate in tokens or dollars (rough order-of-magnitude). Helps the user decide when to escalate to Opus or run multiple competing plans.

**N4. Branching for creative exploration (Spec Kit pattern).** L4 projects: generate `plan-A.md` and `plan-B.md` from the same `spec.md`, optimizing for different goals (speed vs. cost vs. maintainability). User picks one, the other is preserved as an ADR alternative.

**N5. Hook recipes shipped as optional companion files.** Don't enable by default, but ship `hooks/` examples:
- A Stop hook that warns if `tasks.md` has unchecked items.
- A PostToolUse hook that runs the verification harness after Edit operations on plan files.
- A SessionStart hook that reads `spec.md` if present and primes context.

**N6. Optional MCP integrations documented.** Especially Context7 (live library docs), GitHub MCP (issue linking), filesystem MCP (large-repo navigation). Not required, but the skill should call out which sub-phases benefit.

**N7. Output a small machine-readable header.** YAML frontmatter at the top of `plan.md` with `level`, `model_tier`, `created_at`, `requirement_count`, `task_count`, `status`. Enables future automation (dashboards, drift checks, CI integration).

**N8. Consider renaming or namespacing.** Anthropic's `/ultraplan` (cloud planning surface) is a distinct, official feature that ships in Claude Code v2.1.91+. As that feature matures, naming collision will confuse users. Consider `deep-plan`, `solo-plan`, `troy-plan`, or namespacing as `tdavis:ultra-plan`. (You already namespace via `personal-plugin@troys-plugins`, but the skill name itself is what shows up in `/help`.)

---

## 5. Specific Suggestions Summary (the "bones" of the rewrite)

### 5.1 Phases the rewritten SKILL.md should have

1. **Phase 0 — Constitution Check** (new)
2. **Phase 1 — Scale Classification (L0–L4)** (new)
3. **Phase 2 — Discovery Interview** (preserved; refined to use AskUserQuestion in batches; capped at ~60 questions; scaled to L)
4. **Phase 3 — Parallel Research** (preserved; formalized as named forked sub-agents)
5. **Phase 4 — Spec authoring** (`spec.md`, EARS-notation acceptance criteria) (new artifact split)
6. **Phase 5 — Plan authoring** (`plan.md`, file-path-grounded, model-tier hints, context budget) (refined)
7. **Phase 6 — Tasks decomposition** (`tasks.md`, parseable checklist, dependency-ordered, R-id traceability) (new artifact split)
8. **Phase 7 — Verification Harness** (failing tests, DoD contract, traceability matrix) (new)
9. **Phase 8 — Risk Register & Self-Review** (preserved + expanded)
10. **Phase 9 — Approval Gate** (explicit user approval before any Implement skill is allowed to run) (new)

Optional second invocation mode: `--refresh` (Phase R: drift detection).

### 5.2 Templates to include in `references/`

- `constitution-template.md`
- `spec-template.md` (with EARS examples)
- `plan-template.md`
- `tasks-template.md` (Spec Kit–compatible)
- `adr-template.md`
- `risk-register-template.md`
- `dod-checklist-template.md`
- `verification-harness-template.md`
- `agents-md-companion-template.md`
- `anti-patterns.md` (expanded)

### 5.3 Anti-patterns to call out explicitly in SKILL.md

- "TBD"/"implement later"/placeholder pollution
- Claiming tests pass without running them
- Vague file references ("somewhere in the API layer")
- Adding scope mid-plan without re-running discovery
- Free-form acceptance criteria that can't be tested
- Self-review without running the actual verification commands
- Picking a stack the constitution forbids
- Generating multiple alternatives instead of one recommendation (your existing rule — keep this)
- Skipping the constitution gate "this time"
- Using "I'll handle that during implementation" for any spec ambiguity
- Generating tasks that reference symbols not defined elsewhere in the plan

### 5.4 Claude Code feature integration points

| Feature | How `ultra-plan` should use it |
|---|---|
| **Plan Mode** | Enter automatically for phases 2–9; rely on its read-only enforcement; avoid duplicating that logic. |
| **`AskUserQuestion`** | Use for all clarifications, batched 5–8 per call. |
| **Skills (`context: fork`)** | Explore-codebase, research-libraries, research-domain are forked sub-skills. |
| **Sub-agents (Agent tool)** | Invoke a Plan-typed subagent for the architectural-design lens; optionally a second one with a different lens for L3+ creative exploration. |
| **Hooks** | Ship optional Stop/PostToolUse/SessionStart recipes — don't auto-install. |
| **MCP** | Document Context7, GitHub, Playwright, filesystem MCPs as optional research enhancers. |
| **CLAUDE.md** | Read at session start; constitution overrides where they conflict (and the conflict is logged). |
| **AGENTS.md** | Read alongside CLAUDE.md; emit one as output if not present. |
| **`/memories` tool** | Use for cross-session continuity in L3/L4 projects. |
| **Ultrathink** | Enabled for Phase 5 (architectural decisions). |
| **Slash commands** | Ship `/ultra-plan`, `/ultra-plan-refresh`, `/ultra-plan-status` (reads frontmatter from current `plan.md`). |
| **Plugins** | Ship as part of `personal-plugin`; declare dependency on no other skills. |

---

## 6. Key Sources & References

The user can dig deeper into these — all were validated during this research:

**Spec-driven canon**
- GitHub Spec Kit repo & docs — `github/spec-kit`, especially `spec-driven.md` and the constitution + plan templates.
- "Spec-driven development with AI" — GitHub Blog post.
- Spec Kit DeepWiki (`deepwiki.com/github/spec-kit`) — best technical explanation of phase gates.
- Microsoft Learn — Implement Spec-Driven Development modules (greenfield + brownfield).
- Kiro docs — `kiro.dev/docs/specs/` and the introducing-Kiro post; InfoQ "Beyond Vibe Coding" article.
- Tessl: "A look at Spec Kit, GitHub's spec-driven software development toolkit."

**BMAD**
- `bmad-code-org/BMAD-METHOD` repo (v6 in flight).
- AngelHack DevLabs: "What is the BMad Method? A Simple Guide."
- Redreamality: "BMAD-METHOD Guide."
- Benny's Mind Hack: "Applied BMAD — Reclaiming Control in AI Development."

**Anthropic primary sources**
- "Effective context engineering for AI agents" — Anthropic Engineering Blog (Sep 2025).
- "Effective harnesses for long-running agents" — Anthropic Engineering Blog.
- "Building Effective AI Agents" — Anthropic Research.
- "Writing effective tools for AI agents" — Anthropic Engineering.
- "Scaling Managed Agents" — Anthropic Engineering.
- "How Anthropic teams use Claude Code" — Anthropic PDF.
- Claude Code docs: `code.claude.com/docs/en/best-practices`, `common-workflows`, `skills`, `ultraplan`.
- Claude Cookbook: "Context engineering: memory, compaction, and tool clearing."

**Practitioner long-form**
- Armin Ronacher: "Agentic Coding Recommendations," "Agent Design Is Still Hard," "Agentic Coding Things That Didn't Work," "A Year of Vibes," "A Language for Agents."
- Simon Willison's claude-code tag and "Agentic Engineering Patterns" Substack post.
- Mitchell Hashimoto on Pragmatic Engineer (covered well in TeamDay.ai writeup, Serenities AI summary).
- Geoffrey Huntley: `ghuntley.com/ralph/`, `ghuntley/how-to-ralph-wiggum` repo; HumanLayer "Brief History of Ralph."
- `inmve/awesome-ai-coding-techniques` (multilingual practitioner anthology).
- Steve Kinney: "Claude Ultraplan: Planning in the Cloud, Executing Wherever."

**Adjacent skills worth reading**
- `6missedcalls/ultraplan` SKILL.md (spiritual cousin; share useful prose).
- `obra/superpowers` — `skills/writing-plans/SKILL.md` (the "no placeholders" rule is gold).
- `OthmanAdi/planning-with-files` (Manus pattern, persistent markdown).
- `openai/skills` — `.experimental/create-plan/SKILL.md` (minimal counterpoint; useful for L0/L1 templates).
- `terraphim/codex-skills/skills/disciplined-verification/SKILL.md` (verification phase reference).
- `shanraisshan/claude-code-best-practice` (community-curated).

**Standards / cross-tool**
- `agents.md` and `agentsmd/agents.md` repo.
- OpenAI Codex docs on AGENTS.md hierarchy (`developers.openai.com/codex/guides/agents-md`).

---

## Caveats

- **The reconstructed snapshot of `ultra-plan` may diverge from your actual SKILL.md** in specifics (phase names, exact discovery question count, artifact paths). The framework-level recommendations remain valid but the line-by-line gap items should be re-validated when you paste in the current SKILL.md for the rewrite.
- **Naming collision warning**: Anthropic's first-party `/ultraplan` is a distinct product feature that has been shipping since Claude Code v2.1.91. As Anthropic builds out the feature, expect potential user confusion. Renaming or hard-namespacing your skill is recommended.
- **BMAD v6 is rapidly evolving**: features like Skills Architecture and Sub-Agent inclusion are explicitly marked as in-flight; treat my BMAD references as a snapshot, not a stable target.
- **Several speculative-tone sources** were excluded from the recommendations (notably some "Ultra Plan mode reasoning longer" SEO content). The Anthropic, GitHub, AWS Kiro, Mitchell Hashimoto, Armin Ronacher, Simon Willison, and BMAD canonical sources are the spine of the analysis.
- **Some LLM-skeptic patterns surfaced in research were intentionally not adopted** — e.g., Geoffrey Huntley's "I don't plan, the model knows what a compiler is" stance is a legitimate counter-philosophy but explicitly contradicts the user's brief, which is to *strengthen* an upfront-planning skill. Ralph's `AGENTS.md` + `IMPLEMENTATION_PLAN.md` minimalism is mentioned only as inspiration for the lean L0/L1 templates.
- **The Anthropic ecosystem is moving fast.** Several primitives referenced here (Ultraplan, Managed Agents, `/memories` tool, Skills `context: fork`) are recent enough that exact APIs may shift. The patterns will outlast the API surface; the rewrite should reference patterns first and APIs second.