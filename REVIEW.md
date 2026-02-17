# Architecture Review

Date: 2026-02-16
Repository: `claude-marketplace`
Scope: Read-only architectural audit with technical debt assessment

## Executive Summary

The repository has a clear top-level architecture: a marketplace monorepo with two plugin boundaries (`personal-plugin`, `bpmn-plugin`) and plugin-scoped Python tools. Architecture intent is documented well in ADRs and `CLAUDE.md`.

The main issues are implementation and governance gaps, not missing architecture patterns. The highest risks are:

1. `research-orchestrator` behavior mismatch around missing API keys.
2. CI validation gaps for nested skills.
3. Event-loop blocking risk in async provider implementations.
4. Quality gates that are too weak for the largest/most complex modules.

## Architecture Snapshot

- Pattern: Plugin marketplace monorepo with strict plugin encapsulation.
- Primary boundaries:
  - Marketplace registry: `.claude-plugin/marketplace.json`
  - Plugin metadata: `plugins/*/.claude-plugin/plugin.json`
  - Command/skill contracts: markdown command files + `skills/*/SKILL.md`
  - Tool runtimes: Python packages in `plugins/*/tools/*`
- Runtime surfaces:
  - `research-orchestrator`
  - `visual-explainer`
  - `feedback-docx-generator`
  - `bpmn2drawio`

## Findings

### Critical (Must Fix)

1. Missing API key behavior is inconsistent and currently unsafe for operator expectations.
- Evidence:
  - `plugins/personal-plugin/tools/research-orchestrator/src/research_orchestrator/cli.py`
  - `plugins/personal-plugin/tools/research-orchestrator/src/research_orchestrator/orchestrator.py`
- Why it matters:
  - Current paths and messaging have conflicted intent (warn vs fail-fast semantics).
  - This creates unpredictable run behavior.
- Decision:
  - If any required API key is missing, throw an error and provide fix instructions.

2. CI frontmatter validation misses nested skills in some checks.
- Evidence:
  - `.github/workflows/validate.yml`
  - `docs/adr/0001-skill-directory-structure.md`
- Why it matters:
  - Invalid or non-compliant skills can pass CI if checks do not target `skills/*/SKILL.md`.

### High (Should Fix Soon)

1. Sync SDK calls inside async provider code can block concurrency.
- Evidence:
  - `plugins/personal-plugin/tools/research-orchestrator/src/research_orchestrator/providers/openai.py`
  - `plugins/personal-plugin/tools/research-orchestrator/src/research_orchestrator/providers/anthropic.py`
- Why it matters:
  - Reduced throughput and responsiveness under multi-provider workloads.

2. Quality gates are weak for high-complexity modules.
- Evidence:
  - Coverage floor for `visual-explainer` is low in CI relative to module size.
  - Type checks are non-blocking for key jobs in `.github/workflows/test.yml`.
- Why it matters:
  - Increases regression risk in the largest and most volatile code paths.

### Medium (Should Fix)

1. Multiple modules use `load_dotenv(override=True)` at runtime.
- Evidence:
  - `plugins/personal-plugin/tools/research-orchestrator/src/research_orchestrator/config.py`
  - `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/config.py`
  - `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/cli.py`
- Why it matters:
  - Environment precedence can become surprising and hard to debug.

2. Falsy-value handling bug pattern in config composition (`x or default`).
- Evidence:
  - `plugins/personal-plugin/tools/visual-explainer/src/visual_explainer/config.py`
- Why it matters:
  - Valid explicit values can be overwritten by defaults.

3. Shared mutable namespace map risk in BPMN parser.
- Evidence:
  - `plugins/bpmn-plugin/tools/bpmn2drawio/src/bpmn2drawio/parser.py`
- Why it matters:
  - Potential state bleed if parser instances mutate shared mappings.

4. Converter merge logic appears inconsistent.
- Evidence:
  - `plugins/bpmn-plugin/tools/bpmn2drawio/src/bpmn2drawio/converter.py`
- Why it matters:
  - Theme/config merge intent is unclear and may silently ignore expected behavior.

### Low (Could Fix)

1. `.env` handling needs policy hardening.
- Evidence:
  - `.env` exists in repo root while `.gitignore` also ignores `.env`.
- Why it matters:
  - Can confuse contributors and increase accidental leakage risk.

2. Broad exception handling in many runtime paths.
- Why it matters:
  - Reduces error specificity and post-incident diagnosability.

## Recommendations

### Immediate

1. Enforce strict API key preflight for `research-orchestrator`.
- Behavior:
  - Require all three keys: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`.
  - If any are missing, fail with exit code `1`.
  - Print concrete remediation steps.
- Suggested error block:
  - Missing required API keys.
  - Set keys in `.env` (or environment):
    - `ANTHROPIC_API_KEY`
    - `OPENAI_API_KEY`
    - `GOOGLE_API_KEY`
  - Then re-run `research-orchestrator check-ready`.

2. Fix CI to validate nested skills correctly.
- Update `validate.yml` checks to scan `skills/*/SKILL.md` everywhere frontmatter is validated.

3. Standardize `.env` policy.
- Recommendation for this project:
  - Keep `.env` out of git.
  - Add and maintain `.env.example` with placeholders only.
  - Add CI guardrails to block committed secrets and accidental `.env` files.

### Short Term (1-2 Weeks)

1. Reduce blocking in async provider execution.
- Use async SDK surfaces where available.
- Wrap unavoidable blocking calls in worker threads.

2. Strengthen CI quality gates.
- Make mypy blocking for stable packages first (`bpmn2drawio`, `feedback-docx-generator`).
- Keep temporary non-blocking status only where necessary with explicit sunset dates.
- Raise `visual-explainer` coverage floor incrementally.

3. Add targeted tests for current high-risk behavior.
- Missing-key fail-fast integration tests.
- CI-style tests for nested skill discovery/validation assumptions.

### Strategic

1. Decompose `visual-explainer` orchestration surface.
- Split CLI, service orchestration, and IO layers for easier testing and lower coupling.

2. Centralize runtime configuration precedence.
- Define and document one rule set for CLI args, `.env`, and process environment.
- Avoid implicit override behavior in module import side effects.

## Prioritized Remediation Roadmap

### Quick Wins (< 1 day)

1. Strict API key fail-fast + instructions in `research-orchestrator`.
- Risk: Low
- Effort: S
- Dependencies: None

2. CI nested-skill scan fix in `validate.yml`.
- Risk: Low
- Effort: S
- Dependencies: None

3. Add `.env.example` and CI secret guardrails.
- Risk: Low
- Effort: S
- Dependencies: None

### Short-Term (1-2 weeks)

1. Async provider blocking mitigation.
- Risk: Medium
- Effort: M
- Dependencies: API preflight behavior stabilization

2. CI gate tightening and coverage ratchet plan.
- Risk: Medium
- Effort: M
- Dependencies: Current failing type/coverage issues triage

### Strategic Initiatives

1. `visual-explainer` modularization.
- Risk: Medium
- Effort: L
- Dependencies: Test expansion + gate hardening

2. Config bootstrap standardization across tools.
- Risk: Medium
- Effort: M
- Dependencies: Agreement on env precedence policy

## Final Recommendations Based on Maintainer Decisions

1. API keys: Enforce strict fail-fast if any required key is missing.
2. `.env`: Use `.env.example` only in git; keep `.env` untracked; add automated secret checks.
3. CI: Move toward blocking type checks and higher coverage floors, starting with lower-risk packages.
