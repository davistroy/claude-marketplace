---
name: prime
description: Evaluate an existing codebase to produce a detailed report on project purpose, health, status, and recommended next steps
---

# Prime

Perform a comprehensive evaluation of the current codebase/project and produce a structured report covering what the project is, where it stands, and what should happen next. This is the skill to use when encountering any project for the first time, resuming work after a break, or needing a full situational assessment before making decisions.

**This skill is read-only. It NEVER modifies files, commits, or pushes.**

## Input

**Arguments:** `$ARGUMENTS`

Optional arguments:
- A specific focus area (e.g., "testing", "deployment readiness", "documentation")
- A path to a subdirectory to scope the analysis

If no arguments are provided, evaluate the entire project from the repository root.

## Instructions

Execute ALL phases below. Use the Task tool with `subagent_type=Explore` for broad codebase searches to avoid flooding context. Use Glob, Grep, and Read directly for targeted lookups.

### Phase 1: Project Identity

Determine what this project IS.

1. **Read project manifests** -- Check for `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, `Gemfile`, `*.csproj`, `Makefile`, `docker-compose.yml`, or similar. Extract: project name, version, description, language/runtime, declared dependencies.
2. **Read documentation** -- Check for `README.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `docs/`, `wiki/`. Extract: stated purpose, architecture overview, setup instructions.
3. **Scan entry points** -- Identify main entry points (`main.*`, `index.*`, `app.*`, `__main__.py`, `cli.*`, `server.*`). Trace the top-level execution flow.
4. **Identify project type** -- Classify as: library, CLI tool, web application, API service, plugin/extension, monorepo, data pipeline, mobile app, infrastructure-as-code, or other.

**Output for report:** Project name, type, language(s), purpose (1-3 sentences), key dependencies.

### Phase 2: Repository Health

Assess the project's current state and activity.

1. **Git history analysis:**
   ```bash
   git log --oneline -20                           # Recent activity
   git log --format='%ai' -1                       # Last commit date
   git log --format='%ai' --reverse | head -1      # First commit date
   git shortlog -sn --no-merges | head -10          # Top contributors
   git log --since="30 days ago" --oneline | wc -l  # Activity last 30 days
   ```

2. **Branch status:**
   ```bash
   git branch -a --sort=-committerdate | head -10   # Active branches
   git status -s                                     # Working tree state
   ```

3. **Open work detection** -- Check for: `TODO`, `FIXME`, `HACK`, `XXX` comments across source files. Check for `IMPLEMENTATION_PLAN.md`, `PROGRESS.md`, `RECOMMENDATIONS.md`, open GitHub issues/PRs if `gh` is available.

4. **Dependency freshness** -- Check lock files for staleness. Note any pinned versions that might be outdated. Check for security advisory files or `npm audit`/`pip-audit` results if available.

**Output for report:** Repository age, activity level (active/maintained/stale/abandoned), contributor count, working tree status, open work items.

### Phase 3: Code Quality & Architecture

Evaluate the codebase structure and quality.

1. **Project structure** -- Map the directory tree (top 3 levels). Identify the architectural pattern: monolith, microservices, plugin architecture, layered, hexagonal, MVC, etc.

2. **Code metrics:**
   - Total source files (by language)
   - Approximate lines of code (use `wc -l` on source files, exclude node_modules, venv, build artifacts)
   - Largest files (potential god classes/modules)
   - Circular dependency indicators

3. **Test coverage:**
   - Test directory presence and structure
   - Test count (if runnable without setup)
   - Coverage configuration (pytest-cov, jest --coverage, etc.)
   - Test-to-source ratio

4. **CI/CD pipeline:**
   - Check `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `Dockerfile`, etc.
   - What does CI run? (lint, test, build, deploy)
   - Are there quality gates? (coverage thresholds, linting enforcement)

5. **Configuration & secrets:**
   - `.env` files (check .gitignore coverage)
   - Config files and their complexity
   - Secret management approach

6. **Code quality signals:**
   - Linter configuration (eslint, ruff, clippy, golangci-lint)
   - Type checking (TypeScript, mypy, pyright)
   - Pre-commit hooks
   - Code formatting enforcement

**Output for report:** Architecture pattern, code size, test coverage status, CI/CD maturity, quality tooling summary.

### Phase 4: Documentation & Developer Experience

Assess how easy it is to understand and work with this project.

1. **Documentation completeness:**
   - README: Does it explain setup, usage, and contribution?
   - API documentation (if applicable)
   - Architecture Decision Records (ADRs)
   - Inline code comments (density and quality)
   - CLAUDE.md or similar AI-context files

2. **Developer onboarding:**
   - Can a new developer set up the project from README alone?
   - Are there development scripts (`make dev`, `npm run dev`, `docker-compose up`)?
   - Is there a `CONTRIBUTING.md`?

3. **Dependency documentation:**
   - Are system dependencies documented?
   - Are environment variables documented?
   - Are third-party service requirements listed?

**Output for report:** Documentation grade (A-F), onboarding friction points, missing documentation.

### Phase 5: Risk Assessment

Identify potential problems and blockers.

1. **Technical debt indicators:**
   - Large files with high complexity
   - Duplicated code patterns
   - Deprecated dependency usage
   - TODO/FIXME density
   - Disabled tests

2. **Security posture:**
   - Hardcoded credentials or API keys
   - `.env` in git history
   - Dependency vulnerabilities (if audit tools available)
   - Input validation patterns

3. **Operational risks:**
   - Single points of failure
   - Missing error handling patterns
   - No monitoring/logging infrastructure
   - Missing backup/recovery procedures

**Output for report:** Risk items categorized as Critical/High/Medium/Low.

### Phase 6: Recommended Next Steps

Based on ALL findings, produce a prioritized action plan.

1. **Immediate actions** (do now, < 1 hour each):
   - Critical security fixes
   - Broken CI/tests
   - Missing .gitignore entries

2. **Short-term improvements** (this week):
   - Documentation gaps
   - Test coverage gaps
   - Dependency updates
   - Code quality quick wins

3. **Strategic initiatives** (plan and schedule):
   - Architectural improvements
   - New feature opportunities
   - Performance optimizations
   - Scalability preparations

4. **Suggested first task:**
   - Based on the full analysis, recommend the single most impactful thing to do next
   - Explain WHY this is the highest-leverage action

## Output

Present findings as a structured in-conversation report with this format:

```markdown
# Project Prime Report
**Project:** [name]
**Generated:** [date]
**Scope:** [full repo | specific path]

---

## 1. Project Identity

| Field | Value |
|-------|-------|
| Name | [name] |
| Type | [library/CLI/webapp/API/etc.] |
| Language(s) | [primary, secondary] |
| Version | [current version or "unversioned"] |
| Purpose | [1-3 sentence description] |

**Key Dependencies:** [top 5-10 dependencies with purpose]

---

## 2. Repository Health

| Metric | Value |
|--------|-------|
| Age | [first commit to now] |
| Last Activity | [last commit date] |
| Activity Level | [Active/Maintained/Stale/Abandoned] |
| Contributors | [count] |
| Working Tree | [Clean/Modified/Uncommitted changes] |
| Open Work | [IMPLEMENTATION_PLAN items, TODOs, issues] |

---

## 3. Code Quality & Architecture

| Metric | Value |
|--------|-------|
| Architecture | [pattern] |
| Source Files | [count by language] |
| Lines of Code | [approximate] |
| Test Files | [count] |
| Test Coverage | [percentage or "not configured"] |
| CI/CD | [present/absent, what it runs] |
| Linting | [tool and status] |
| Type Checking | [tool and status] |

**Largest Modules:** [top 3-5 files by size]

---

## 4. Documentation

| Aspect | Grade | Notes |
|--------|-------|-------|
| README | [A-F] | [what's good/missing] |
| Setup Guide | [A-F] | [can you get running from docs alone?] |
| API Docs | [A-F or N/A] | [coverage level] |
| Architecture Docs | [A-F] | [ADRs, diagrams, etc.] |
| Code Comments | [A-F] | [density and quality] |
| **Overall** | **[A-F]** | |

---

## 5. Risk Assessment

### Critical
- [item or "None identified"]

### High
- [items]

### Medium
- [items]

### Low
- [items]

---

## 6. Recommended Next Steps

### Immediate (< 1 hour)
1. [action] -- [why]

### Short-term (this week)
1. [action] -- [why]
2. [action] -- [why]

### Strategic (plan & schedule)
1. [action] -- [why]

### Suggested First Task
> [Specific, actionable recommendation with rationale]

---

*Report generated by /prime on [date]*
```

## Example

```yaml
User: /prime

Claude: [Analyzes the codebase across all 6 phases]

# Project Prime Report
**Project:** claude-marketplace
**Generated:** 2026-02-16
...
[Full structured report]
```

```yaml
User: /prime testing

Claude: [Focuses analysis on testing infrastructure and coverage]

# Project Prime Report (Focus: Testing)
...
```

```yaml
User: /prime plugins/bpmn-plugin

Claude: [Scopes analysis to the bpmn-plugin subdirectory]

# Project Prime Report
**Project:** bpmn-plugin
**Scope:** plugins/bpmn-plugin
...
```

## Error Handling

- If not in a git repository: Note this in the report, skip git-dependent analysis, proceed with file-based analysis
- If project is empty or near-empty: Produce abbreviated report noting the project appears to be in initial scaffolding phase
- If a specific tool (gh, npm, pip) is unavailable: Skip that check, note it as "unable to assess" in the report
- If the project is extremely large (>10,000 files): Use sampling -- analyze representative directories rather than exhaustive scan
- If arguments specify a path that doesn't exist: Report the error and fall back to full repository analysis

## Performance

| Project Size | Expected Duration |
|--------------|-------------------|
| Small (< 50 files) | 30-60 seconds |
| Medium (50-200 files) | 1-3 minutes |
| Large (200-500 files) | 3-5 minutes |
| Very Large (500+ files) | 5-10 minutes |
