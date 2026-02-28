---
description: Quick architectural audit with technical debt assessment (read-only, no files generated)
allowed-tools: Read, Glob, Grep
---

# Review Architecture

**READ-ONLY COMMAND — DO NOT MAKE ANY CHANGES TO FILES. ONLY ANALYZE AND REPORT.**

Perform a quick architectural audit of this project. This command provides an in-conversation analysis without generating files. For a comprehensive analysis with saved RECOMMENDATIONS.md and IMPLEMENTATION_PLAN.md, use `/plan-improvements` instead.

## Input Validation

Before proceeding, verify:
- This is a code project (not just documentation or data)
- Project structure is readable and contains source files
- The codebase has sufficient complexity to warrant architectural review (not a single-file script)

For single-file projects or simple scripts, provide a brief assessment rather than a full architectural audit.

## Phase 1: Codebase Reconnaissance

Execute these tasks to map the project:

1. **Map project structure** — Run `ls` and glob patterns to identify the directory layout, tech stack, and primary language(s)
2. **Identify architectural pattern** — Determine the pattern(s) in use (MVC, microservices, monolith, hexagonal, event-driven, etc.) by examining entry points, module organization, and dependency flow
3. **Catalog dependencies** — Read package manifests (package.json, requirements.txt, Cargo.toml, go.mod, etc.) and note versions, counts, and any obviously outdated packages
4. **Trace system boundaries** — Identify entry points, public APIs, data stores, and external integrations
5. **Map data flow** — Trace the 3 most common user-facing workflows from entry point through to data persistence or response

## Phase 2: Architectural Assessment

Evaluate each dimension using the imperative tasks below. For each dimension, assign a rating from the Architecture Scorecard scale.

### Rating Scale

| Rating | Label | Meaning |
|--------|-------|---------|
| 5 | Excellent | Best-in-class, no significant issues |
| 4 | Good | Solid with minor improvements possible |
| 3 | Adequate | Functional but has notable gaps |
| 2 | Poor | Significant issues impacting quality or velocity |
| 1 | Critical | Fundamental problems requiring immediate attention |

### Dimension 1: Structure & Organization

1. **Trace module boundaries** — Map the dependency graph between top-level modules/packages. Identify any circular dependencies.
2. **Evaluate separation of concerns** — Check if business logic, data access, presentation, and infrastructure are cleanly separated or entangled.
3. **Assess folder-architecture alignment** — Determine whether the directory structure reflects the actual architecture or fights against it.
4. **Check layer violations** — Look for cases where lower layers depend on higher layers or cross-cutting concerns leak into domain logic.

### Dimension 2: Code Quality

1. **Scan for DRY violations** — Identify copy-paste code clusters where 3+ lines of similar logic appear in multiple locations.
2. **Find god modules** — Locate files or classes exceeding ~500 lines or handling 3+ unrelated responsibilities.
3. **Check abstraction consistency** — Verify that functions/methods operate at a single abstraction level without mixing high-level orchestration with low-level details.
4. **Assess error handling** — Determine if error handling follows a consistent strategy (exceptions, result types, error codes) or is ad-hoc.

### Dimension 3: Dependency Management

1. **Check for outdated packages** — Compare installed versions against latest available. Flag any packages more than 2 major versions behind.
2. **Identify unnecessary dependencies** — Look for packages that could be replaced with standard library functions or that duplicate functionality.
3. **Assess lock file health** — Verify lock files exist and are committed. Check for version pinning strategy.
4. **Evaluate dependency depth** — Note transitive dependency count and any packages pulling in disproportionately large dependency trees.

### Dimension 4: Testing

1. **Measure test coverage** — Check for test files, test configuration, and estimate coverage (file count ratio at minimum).
2. **Evaluate test architecture** — Determine if tests are unit, integration, or e2e. Check for proper isolation and mocking boundaries.
3. **Check test quality** — Sample 3-5 test files. Look for assertions, edge case coverage, and meaningful test names.
4. **Assess CI integration** — Check for CI configuration files and whether tests run automatically.

### Dimension 5: Security

1. **Scan for hardcoded secrets** — Search for API keys, passwords, tokens, or connection strings in source files.
2. **Check input validation** — Trace 2-3 user input paths from entry to processing. Verify inputs are validated and sanitized.
3. **Assess authentication/authorization** — Identify auth patterns and check for proper middleware, token validation, and role checks.
4. **Review dependency vulnerabilities** — Check for known CVE advisories in dependency manifests.

### Dimension 6: Performance & Scalability

1. **Identify N+1 patterns** — Look for loops that make individual database queries or API calls instead of batching.
2. **Check for blocking operations** — In async codebases, search for synchronous I/O or CPU-intensive operations blocking the event loop.
3. **Assess resource management** — Verify connections, file handles, and other resources are properly cleaned up.
4. **Evaluate caching strategy** — Note whether caching is used where appropriate and if invalidation is handled.

## Phase 3: Technical Debt Inventory

Categorize all identified issues using severity levels:

| Severity | Label | Description |
|----------|-------|-------------|
| **CRITICAL** | Must fix | Security vulnerabilities, data integrity risks, production stability threats |
| **HIGH** | Should fix | Architectural violations that impede feature development |
| **MEDIUM** | Could fix | Code quality issues that slow velocity |
| **LOW** | Nice to have | Style inconsistencies, minor optimizations |

For each finding, include:
- **ID**: Sequential identifier (e.g., F1, F2, F3)
- **Severity**: CRITICAL / HIGH / MEDIUM / LOW
- **Dimension**: Which assessment dimension it falls under
- **Description**: What the issue is and why it matters
- **Location**: Specific files and line numbers
- **Remediation**: Concrete fix approach

## Phase 4: Remediation Roadmap

Produce a prioritized action plan organized by effort level:

| Size | File Count | Estimated LOC | Typical Duration |
|------|-----------|---------------|------------------|
| **S** | 1-3 files | < 100 LOC | < 1 day |
| **M** | 3-8 files | 100-400 LOC | 1-3 days |
| **L** | 8-15 files | 400-1000 LOC | 3-7 days |
| **XL** | 15+ files | 1000+ LOC | 1-2 weeks |

For each remediation item include:
- Specific files/modules affected
- Concrete refactoring approach
- Risk level (low/medium/high)
- Dependencies on other items
- Effort estimate (S/M/L/XL)

Organize into:
1. **Quick wins** (S effort, high impact) — Build momentum
2. **Short-term targets** (M effort) — Important refactors
3. **Strategic initiatives** (L effort) — Architectural changes requiring planning
4. **Long-term considerations** (XL effort) — Major rewrites or migrations

## Structured Output Template

Present findings using this structure:

### Executive Summary
2-3 paragraphs covering: what the project does, overall architecture health, top 3 strengths, and top 3 concerns.

### Architecture Scorecard

```text
| Dimension              | Rating | Notes                              |
|------------------------|--------|------------------------------------|
| Structure & Org        | X/5    | [One-line summary]                 |
| Code Quality           | X/5    | [One-line summary]                 |
| Dependency Management  | X/5    | [One-line summary]                 |
| Testing                | X/5    | [One-line summary]                 |
| Security               | X/5    | [One-line summary]                 |
| Performance            | X/5    | [One-line summary]                 |
|------------------------|--------|------------------------------------|
| **Overall**            | X/5    | [Weighted average, round to 0.5]   |
```

### Findings
Numbered findings with severity tags, organized by dimension.

### Remediation Roadmap
Prioritized list with T-shirt sizes and dependencies.

## Example Scorecard

```text
| Dimension              | Rating | Notes                                      |
|------------------------|--------|--------------------------------------------|
| Structure & Org        | 4/5    | Clean separation, minor layer violations   |
| Code Quality           | 3/5    | Several god modules, inconsistent errors   |
| Dependency Management  | 4/5    | Well-pinned, 2 outdated packages           |
| Testing                | 2/5    | 30% coverage, no integration tests         |
| Security               | 3/5    | No hardcoded secrets, missing input validation |
| Performance            | 4/5    | Good caching, one N+1 pattern found        |
|------------------------|--------|--------------------------------------------|
| **Overall**            | 3.5/5  | Solid foundation, testing is the gap       |
```

## Example Finding

```text
### F3. Inconsistent Error Handling [MEDIUM]
**Dimension:** Code Quality
**Location:** src/api/handlers/*.ts (6 files)
**Description:** API handlers mix try/catch with .catch() chains and some omit error
handling entirely. Three handlers return raw error objects to clients.
**Remediation:** Create a shared error middleware. Wrap all handlers in a standard
try/catch pattern. Estimated effort: M (6 files, ~150 LOC).
```

## Error Handling

| Error Condition | Behavior |
|-----------------|----------|
| **Empty project** | Display: `Error: No source files found in project directory.` Exit. |
| **Project too large** | If 500+ files, display: `Large codebase detected ([N] files). Limiting analysis to top-level modules. Run on specific directories for deeper analysis.` Focus on architecture-level patterns rather than file-level details. |
| **No source code found** | If only documentation/data files exist, display: `This project contains no source code files. Use /assess-document for documentation review.` |
| **Read permission errors** | Skip unreadable files, note them in findings, continue analysis. |

## Execution Guidelines

- Be specific — cite file paths, line numbers, and concrete code examples
- Distinguish between "must fix" (CRITICAL/HIGH) and "could fix" (MEDIUM/LOW)
- Consider the project's maturity and team context when assigning ratings
- Identify any architectural decisions that need documentation (ADRs)
- Flag areas where you need clarification on intent before judging
- Start with reconnaissance and present the executive summary before diving into detailed findings

## Related Commands

- `/plan-improvements` — Comprehensive analysis that generates RECOMMENDATIONS.md and IMPLEMENTATION_PLAN.md
- `/review-intent` — Compare original intent vs current implementation (complementary review)
- `/review-pr` — Review a specific pull request for code quality and security
- `/plan-next` — Get a recommendation for the next action based on current state
