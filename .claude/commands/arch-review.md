---
description: Deep architectural review with technical debt assessment and remediation roadmap
---

You are performing a comprehensive architectural audit of this project. Execute the following systematic analysis:

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

## Execution Instructions
- DO NOT MAKE ANY CHANGES - ONLY ANALYZE AND PRESENT A DETAILED PLAN
- Start with reconnaissance and present your findings before proceeding
- Be specific—cite file paths, line numbers, and concrete code examples
- Distinguish between "must fix" and "should fix" and "could fix"
- Consider the project's maturity and team context when prioritizing
- Identify any architectural decisions that need documentation (ADRs)
- Flag areas where you need clarification on intent before judging

Begin by analyzing the project structure and presenting an executive summary of the architecture before diving into detailed findings.
