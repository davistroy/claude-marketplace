# Learnings

Issues encountered during implementation and their solutions.

---

## Entries

### Phase 1: Quick Wins & Dependency Hygiene

**Issue:** Narrowing `except Exception:` to specific types in layout.py (item 1.5) missed `LayoutError`, which is raised when pygraphviz is unavailable. This caused 69 test failures because the graphviz fallback path stopped working.
**Solution:** Added `LayoutError` to the exception tuple: `except (ImportError, AttributeError, RuntimeError, OSError, LayoutError):`. When narrowing exception handlers, always trace the full call chain to identify all exception types that can be raised.

**Issue:** feedback-docx-generator has no `[dev]` extra in pyproject.toml, so `pip-compile --extra dev` is not applicable.
**Solution:** Generated only `requirements-lock.txt` (7 total files instead of 8).

