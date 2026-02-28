---
description: Quick architectural audit with technical debt assessment (read-only, no files generated)
allowed-tools: Read, Glob, Grep
---

# Review Architecture

Perform a quick architectural audit of this project. This command provides an in-conversation analysis without generating files. For a comprehensive analysis with saved RECOMMENDATIONS.md and IMPLEMENTATION_PLAN.md, use `/plan-improvements` instead.

## Input Validation

Before proceeding, verify:
- This is a code project (not just documentation or data)
- Project structure is readable and contains source files
- The codebase has sufficient complexity to warrant architectural review (not a single-file script)

For single-file projects or simple scripts, provide a brief assessment rather than a full architectural audit.

## Overview

Execute the following systematic analysis:

## Phase 1: Codebase Reconnaissance
1. Map the complete project structure and identify the tech stack
2. Determine the architectural pattern(s) in use (MVC, microservices, monolith, hexagonal, etc.)
3. Catalog all external dependencies and their versions
4. Identify entry points, public APIs, and system boundaries
5. Trace data flow patterns and state management approaches

## Phase 2: Architectural Assessment
Evaluate each dimension against industry best practices:

**Structure & Organization**
- Is there clear separation of concerns?
- Are module/package boundaries logical and enforced?
- Is the dependency graph clean or are there circular dependencies?
- Does the folder structure reflect the architecture or fight against it?

**Code Quality Patterns**
- DRY violations and copy-paste code clusters
- God classes/modules that do too much
- Leaky abstractions and broken encapsulation
- Inconsistent error handling strategies
- Mixed abstraction levels within functions/methods

**Security Posture**
- Hardcoded secrets or credentials
- Input validation gaps
- Authentication/authorization patterns
- Dependency vulnerabilities (outdated packages with known CVEs)

**Testability & Reliability**
- Test coverage and test architecture
- Dependency injection vs hard-coded dependencies
- Mocking boundaries and test isolation
- Error recovery and resilience patterns

**Performance & Scalability**
- N+1 queries and inefficient data access patterns
- Missing caching opportunities
- Blocking operations in async contexts
- Resource cleanup and memory management

**Developer Experience**
- Build/deployment complexity
- Configuration management approach
- Local development friction points
- Onboarding barriers for new developers

## Phase 3: Technical Debt Inventory
Create a categorized inventory of all identified issues:
- **Critical**: Security vulnerabilities, data integrity risks, production stability threats
- **High**: Architectural violations that impede feature development
- **Medium**: Code quality issues that slow velocity
- **Low**: Style inconsistencies, minor optimizations, nice-to-haves

## Phase 4: Remediation Roadmap
Produce a prioritized action plan with:
1. **Quick wins**: Low-effort, high-impact fixes to build momentum (< 1 day each)
2. **Short-term targets**: Important refactors achievable in 1-2 weeks
3. **Strategic initiatives**: Larger architectural changes requiring planning
4. **Long-term considerations**: Major rewrites or migrations to evaluate

For each item include:
- Specific files/modules affected
- Concrete refactoring approach
- Risk level of the change
- Dependencies on other remediation items
- Estimated effort (T-shirt sizing)

## Performance

**Typical Duration:**

| Codebase Size | Expected Time |
|---------------|---------------|
| Small (< 50 files) | 30-60 seconds |
| Medium (50-200 files) | 1-3 minutes |
| Large (200-500 files) | 3-7 minutes |
| Very Large (500+ files) | 7-15 minutes |

**Factors Affecting Performance:**
- **File count**: Primary driver of analysis time
- **Code complexity**: Deeply nested or tightly coupled code takes longer
- **Language count**: Multi-language projects require broader analysis
- **Dependency depth**: Projects with many dependencies take longer

**What to Expect:**
- Phase 1 (Reconnaissance): 20-40% of total time
- Phase 2 (Assessment): 30-40% of total time
- Phase 3 (Debt Inventory): 15-25% of total time
- Phase 4 (Roadmap): 10-20% of total time

**Signs of Abnormal Behavior:**
- No output after 3 minutes on small projects
- Stuck reading the same files repeatedly
- Error messages about file access or parsing

**If the command seems stuck:**
1. Check for phase progress indicators
2. Wait at least 5 minutes for medium/large codebases
3. If no activity, interrupt and retry
4. For very large projects, consider running on specific directories first

---

## Execution Instructions
- DO NOT MAKE ANY CHANGES - ONLY ANALYZE AND PRESENT A DETAILED PLAN
- Start with reconnaissance and present your findings before proceeding
- Be specific—cite file paths, line numbers, and concrete code examples
- Distinguish between "must fix" and "should fix" and "could fix"
- Consider the project's maturity and team context when prioritizing
- Identify any architectural decisions that need documentation (ADRs)
- Flag areas where you need clarification on intent before judging

Begin by analyzing the project structure and presenting an executive summary of the architecture before diving into detailed findings.
