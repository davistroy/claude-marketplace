---
description: Quick architectural audit with technical debt assessment (read-only, no files generated)
argument-hint: "[--json] [--focus <dimensions>]"
effort: high
allowed-tools: Read, Glob, Grep
---

# Review Architecture

**READ-ONLY COMMAND — DO NOT MAKE ANY CHANGES TO FILES. ONLY ANALYZE AND REPORT.**

Perform a quick architectural audit of this project. This command provides an in-conversation analysis without generating files. For a comprehensive analysis with saved RECOMMENDATIONS.md and IMPLEMENTATION_PLAN.md, use `/plan-improvements` instead.

## Input Validation

**Optional Flags:**

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--json` | (none — boolean flag) | off | Output results as structured JSON instead of text. Enables CI/CD pipeline integration and programmatic consumption. |
| `--focus` | Comma-separated dimension names | all dimensions | Limit analysis to specific dimensions. Valid values: `code-quality`, `architecture`, `security`, `performance`, `testing`, `dependencies`. |

**Focus Flag Validation:**
If `--focus` is provided, validate each dimension name. If any are invalid, display:
```text
Error: Invalid focus dimension(s): [invalid-names]

Valid dimensions: code-quality, architecture, security, performance, testing, dependencies

Example: /review-arch --focus security,testing
```

**Dimension Name Mapping:**

| Focus Flag Value | Corresponds To |
|------------------|----------------|
| `architecture` | Dimension 1: Structure & Organization |
| `code-quality` | Dimension 2: Code Quality |
| `dependencies` | Dimension 3: Dependency Management |
| `testing` | Dimension 4: Testing |
| `security` | Dimension 5: Security |
| `performance` | Dimension 6: Performance & Scalability |

Before proceeding, verify:
- This is a code project (not just documentation or data)
- Project structure is readable and contains source files
- The codebase has sufficient complexity to warrant architectural review (not a single-file script)

For single-file projects or simple scripts, provide a brief assessment rather than a full architectural audit.

## Instructions

Follow these phases in sequence. Phase 1 gathers data; Phases 2-3 analyze it; Phase 4 produces the remediation roadmap.

## Phase 1: Codebase Reconnaissance

Execute these tasks to map the project:

1. **Map project structure** — Run `ls` and glob patterns to identify the directory layout, tech stack, and primary language(s)
2. **Identify architectural pattern** — Determine the pattern(s) in use (MVC, microservices, monolith, hexagonal, event-driven, etc.) by examining entry points, module organization, and dependency flow
3. **Catalog dependencies** — Read package manifests (package.json, requirements.txt, Cargo.toml, go.mod, etc.) and note versions, counts, and any obviously outdated packages
4. **Trace system boundaries** — Identify entry points, public APIs, data stores, and external integrations
5. **Map data flow** — Trace the 3 most common user-facing workflows from entry point through to data persistence or response

## Phase 2: Architectural Assessment

**If `--focus` is specified**, only evaluate the dimensions listed. Skip all other dimensions entirely — do not score, analyze, or report on them. At the top of the output, include the note:

```text
Focused analysis — only [dimension1, dimension2, ...] evaluated.
```

**If `--focus` is not specified**, evaluate all dimensions (default behavior unchanged).

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

### Cross-Cutting Analysis (Before Constructing the Roadmap)

Before building the remediation list, review ALL findings from Phases 2-3 together and identify interrelationships:

1. **Shared root causes** — Multiple findings may stem from the same underlying issue (e.g., missing validation layer causes both security and code quality findings). Group these so the roadmap addresses the root cause once rather than patching each symptom independently.
2. **Change interactions** — Fixing finding F3 may conflict with or depend on fixing F7. Map these interactions so the roadmap sequences items correctly and avoids a whack-a-mole cycle where fixing one issue creates another.
3. **Architectural coherence** — Remediation items should collectively move the codebase toward a cleaner architecture, not just patch individual defects. Prefer integrated solutions that address multiple findings through a single well-designed change over isolated fixes that accumulate technical debt.

### Prioritized Action Plan

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

When `--focus` is active, only include rows for the focused dimensions. The Overall score is the average of only the focused dimensions.

### Findings
Numbered findings with severity tags, organized by dimension. When `--focus` is active, only include findings from focused dimensions.

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

## Example: Focused Analysis

```text
User: /review-arch --focus security,testing

Claude:
Focused analysis — only security, testing evaluated.

### Architecture Scorecard

| Dimension              | Rating | Notes                                          |
|------------------------|--------|-------------------------------------------------|
| Testing                | 2/5    | 30% coverage, no integration tests              |
| Security               | 3/5    | No hardcoded secrets, missing input validation   |
|------------------------|--------|-------------------------------------------------|
| **Overall**            | 2.5/5  | Average of focused dimensions                    |

[Findings and remediation for security and testing only...]
```

## JSON Output Mode

When `--json` is specified, output ONLY the JSON to stdout. Do not include any surrounding text, headers, or formatting — just the raw JSON object.

Default behavior (no `--json` flag) is unchanged.

**JSON Output Schema:**

```json
{
  "scorecard": {
    "structure_and_org": "number — rating 1-5",
    "code_quality": "number — rating 1-5",
    "dependency_management": "number — rating 1-5",
    "testing": "number — rating 1-5",
    "security": "number — rating 1-5",
    "performance": "number — rating 1-5",
    "overall": "number — weighted average, rounded to 0.5"
  },
  "findings": [
    {
      "id": "string — sequential identifier (e.g., F1, F2)",
      "severity": "string — CRITICAL | HIGH | MEDIUM | LOW",
      "category": "string — dimension name the finding falls under",
      "description": "string — what the issue is and why it matters",
      "location": "string — specific files and line numbers",
      "recommendation": "string — concrete fix approach"
    }
  ],
  "remediation": [
    {
      "id": "string — sequential identifier (e.g., R1, R2)",
      "effort": "string — S | M | L | XL",
      "impact": "string — low | medium | high",
      "description": "string — specific refactoring approach",
      "files_affected": ["string — list of file paths"],
      "depends_on": ["string — list of remediation IDs this depends on"]
    }
  ]
}
```

---

## Performance

| Codebase Size | Expected Duration |
|---------------|-------------------|
| Small project (< 20 files) | 1-2 minutes |
| Medium project (20-100 files) | 2-5 minutes |
| Large project (100-500 files) | 5-12 minutes |
| Very large project (500+ files) | 12-20 minutes (limited to top-level module analysis) |

Duration scales with the number of source files and the complexity of the dependency graph. Phase 1 (reconnaissance) accounts for roughly 40% of total time due to file scanning and structure mapping. Using `--focus` to limit dimensions reduces time roughly proportionally. The `--json` flag adds negligible overhead. Very large codebases (500+ files) trigger the automatic scoping described in Error Handling, which limits analysis depth.

## Related Commands

- `/plan-improvements` — Comprehensive analysis that generates RECOMMENDATIONS.md and IMPLEMENTATION_PLAN.md
- `/review-intent` — Compare original intent vs current implementation (complementary review)
- `/review-pr` — Review a specific pull request for code quality and security
- `/plan-next` — Get a recommendation for the next action based on current state
