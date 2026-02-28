# Learnings

Issues encountered during implementation and their solutions across three implementation cycles.

---

## Summary

Key learnings synthesized across all implementation cycles (94 work items, 19 phases):

- **Trace the full call chain before narrowing exception handlers.** Changing `except Exception:` to specific types broke 69 tests because `LayoutError` was missed from the fallback path. Always map all propagating exception types before restricting handlers.
- **Audit optional dependency extras before generating lock files.** Not all tools define `[dev]` extras in pyproject.toml, so blanket `pip-compile --extra dev` will fail on some.
- **Cross-cutting batch fixes must go first.** Applying `allowed-tools`, related commands, and dead reference removal in Phase 1 prevented redundant work in later phases. Without this, each subsequent phase would have needed to add these elements individually.
- **Dead references propagate through templates.** Removing `scripts/generate-help.py` from 3 commands was insufficient -- 8 template files and 2 pattern reference files also contained the dead references. Always grep the entire repository after removing any referenced path.
- **Secrets policy enforcement requires both removal and replacement.** Deleting `.env` write instructions without providing the `/unlock` alternative leaves users stranded. Always pair removal with a working alternative.
- **Proactive trigger sections are the highest-value addition for skills.** Without explicit trigger conditions, skills are effectively hidden commands. Adding 3-4 specific trigger conditions per skill makes the entire skill system more discoverable.
- **Quality reviews compound in value.** The RECOMMENDATIONS.md review identified 24 individual issues and 8 systemic patterns. Addressing the 8 systemic patterns first (cross-cutting fixes) resolved roughly 40% of the individual issues as side effects.
- **Plan size limits matter for execution quality.** Capping phases at 6 work items and plans at 8 phases kept each subagent focused. Larger phases produced more inconsistencies in earlier cycles.
- **Flag consistency is a maintenance burden, not a design burden.** The audit (work item 7.5) found inconsistent flag support was not from poor design but from incremental additions over time. A periodic consistency sweep is more practical than trying to enforce consistency at creation time.
- **Shell injection risks hide in `eval` patterns.** The unlock skill's `eval "export KEY=$VALUE"` pattern was rated 5/5 overall but contained a shell injection vector. Security review of even high-rated code is essential for any pattern using `eval` with external data.

---

## Entries

### Phase 1: Quick Wins & Dependency Hygiene

**Issue:** Narrowing `except Exception:` to specific types in layout.py (item 1.5) missed `LayoutError`, which is raised when pygraphviz is unavailable. This caused 69 test failures because the graphviz fallback path stopped working.
**Solution:** Added `LayoutError` to the exception tuple: `except (ImportError, AttributeError, RuntimeError, OSError, LayoutError):`. When narrowing exception handlers, always trace the full call chain to identify all exception types that can be raised.

**Issue:** feedback-docx-generator has no `[dev]` extra in pyproject.toml, so `pip-compile --extra dev` is not applicable.
**Solution:** Generated only `requirements-lock.txt` (7 total files instead of 8).

### Quality Overhaul: Cross-Cutting Batch Fixes

**Issue:** Dead references to `scripts/generate-help.py` and `schemas/` directory existed not only in the 3-5 directly-affected command files but also in 8 template files under `references/templates/` and 2 pattern files. Initial removal missed these secondary locations.
**Solution:** After removing references from the primary files, ran a repository-wide grep for all dead paths. Found and fixed 16 additional references across template and pattern files. Lesson: always do a full-repo search after removing any referenced path.

**Issue:** Removing `.env` write instructions from `research-topic` and `visual-explainer` without providing a replacement would have left users unable to configure API keys.
**Solution:** Replaced `.env` write wizards with references to the `/unlock` skill and added a note pointing to the CLAUDE.md Secrets Management Policy. Retained the list of required API key names so users know what they need.

### Quality Overhaul: Major Overhauls (Phase 2)

**Issue:** The `plan-next` command referenced "Ultrathink" jargon and had no actionable methodology -- just 47 lines of vague instructions.
**Solution:** Complete rewrite to 150+ lines with structured methodology: plan-awareness (checks IMPLEMENTATION_PLAN.md), git-awareness (checks status, branches, PRs), decision matrix (priority ordering), and structured output template. This closed the planning pipeline loop.

### Quality Overhaul: Error Handling Audit (Phase 7)

**Issue:** After completing Phases 2-6, 5 of 32 files still lacked error handling sections: `plan-improvements.md`, `review-intent.md`, `clean-repo.md`, `ask-questions.md`, and `plan-gate/SKILL.md`.
**Solution:** Added error handling sections with consistent table format (Condition | Cause | Action) and 5-8 domain-specific failure modes each. The audit pass was essential -- relying solely on per-phase implementation left gaps.

