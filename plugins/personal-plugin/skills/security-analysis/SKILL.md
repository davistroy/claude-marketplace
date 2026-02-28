---
name: security-analysis
description: Comprehensive security analysis with tech stack detection, vulnerability scanning, and remediation planning
allowed-tools: Read, Glob, Grep, Bash, WebSearch
---

# Security Analysis Framework

Perform a comprehensive security vulnerability scan and analysis of the current project. Identifies the technology stack, scans for vulnerabilities in source code and dependencies, assesses real-world risk with context-aware analysis, and produces an actionable remediation roadmap.

## Input Validation

**Optional Arguments:**
- `<path>` - Directory or file path to analyze (defaults to current working directory)
- `--quick` - Surface scan only: technology detection, dependency audit, and top-level code patterns. Skips deep taint analysis and fuzzing methodology review.
- `--dependencies-only` - Only check dependency vulnerabilities (skip source code analysis)

**Usage:**
```text
/security-analysis                          # Full scan of current project
/security-analysis src/                     # Scan specific directory
/security-analysis --quick                  # Fast surface-level scan
/security-analysis --dependencies-only      # Dependencies only
```

## Proactive Trigger Conditions

Suggest this skill when:
1. The user mentions security, vulnerabilities, CVEs, or audit
2. After scaffolding a new project with `/scaffold-plugin` or similar
3. Before a release, deployment, or merge to production
4. When reviewing code that handles authentication, authorization, or user input
5. When the user adds or updates dependencies (package.json, requirements.txt, etc.)
6. After cloning or pulling a new/unfamiliar repository

## Performance Expectations

- **Quick scan (`--quick`):** 1-3 minutes. Covers technology detection, dependency audit, and surface-level code patterns.
- **Full scan:** 5-15 minutes depending on codebase size. Includes deep taint analysis, data flow tracing, and comprehensive code review.
- **Dependencies-only (`--dependencies-only`):** 1-2 minutes. Runs native audit tools and checks for known CVEs.

## Core Security Analysis Process

### Phase 1: Discovery and Reconnaissance

1. **Technology Stack Detection**: Identify languages, frameworks, and dependencies by scanning for manifest files (package.json, requirements.txt, pom.xml, go.mod, Cargo.toml, etc.)
2. **Attack Surface Mapping**: Enumerate all entry points (APIs, forms, file uploads, CLI arguments, environment variables)
3. **Dependency Inventory**: List all direct and transitive dependencies with version numbers
4. **Configuration Review**: Check for security-relevant configurations (CORS, CSP, auth settings)

### Phase 2: Vulnerability Scanning

#### A. Static Code Analysis

Scan source code for OWASP Top 10 and common vulnerability patterns:
- **Injection Vulnerabilities**: SQL, NoSQL, Command, LDAP, XPath, Template injection
- **Broken Authentication**: Weak password policies, session fixation, credential storage
- **Sensitive Data Exposure**: Hardcoded secrets, unencrypted data, logging sensitive info
- **XML External Entities (XXE)**: Unsafe XML parsing
- **Broken Access Control**: Missing authorization checks, IDOR vulnerabilities
- **Security Misconfiguration**: Default credentials, unnecessary features enabled
- **Cross-Site Scripting (XSS)**: Reflected, Stored, DOM-based
- **Insecure Deserialization**: Unsafe object deserialization
- **Using Components with Known Vulnerabilities**: Outdated dependencies
- **Insufficient Logging and Monitoring**: Missing security event logging

#### B. Dependency Vulnerability Analysis

**IMPORTANT**: Always run native security audit tools FIRST before web search for faster and more accurate results.

For each dependency:
1. **Extract Version Information**: From package manifests
2. **Run Native Security Audit Tools** (Primary Method):
   - **Node.js/JavaScript**: `npm audit` or `npm audit --json`
   - **Python**: `pip-audit` or `safety check`
   - **Java/Maven**: `mvn dependency-check:check`
   - **Java/Gradle**: `./gradlew dependencyCheckAnalyze`
   - **.NET**: `dotnet list package --vulnerable`
   - **PHP/Composer**: `composer audit`
   - **Ruby**: `bundle audit check`
   - **Rust**: `cargo audit`
   - **Go**: `govulncheck ./...`
3. **Parse Audit Results**: Extract CVE IDs, severity levels, and affected versions from tool output
4. **Web Search for CVEs** (Secondary/Verification Method): NVD, Snyk, GitHub Security Advisories
5. **Check Latest Versions**: Compare against current stable releases
6. **Assess Severity**: Use CVSS scores and exploit availability
7. **Verify Patch Availability**: Check if fixes exist and are stable

#### C. Context-Aware Analysis

For each identified vulnerability:
1. **Code Path Tracing**: Is the vulnerable code actually used?
2. **Import Analysis**: Are vulnerable functions imported?
3. **Call Graph Analysis**: Are vulnerable methods called?
4. **Data Flow Analysis**: Does user input reach vulnerable code?
5. **Environment Context**: Is this a dev-only or production dependency?

### Phase 3: Advanced Vulnerability Discovery

Skip this phase if `--quick` flag is set.

#### A. Taint Analysis and Data Flow Tracing
1. **Identify Sources**: Map all entry points (`req.body`, `argv`, `params`, `headers`)
2. **Identify Sinks**: Map dangerous functions (`eval()`, `exec()`, `innerHTML`, `SQL execution`)
3. **Trace Flow**: Trace if input reaches a sink without a sanitizer step
4. **Zero Tolerance**: If ANY user input reaches a sensitive sink without strict validation, flag as CRITICAL

#### B. Logic Abusability
1. **Race Conditions**: Identify concurrent state updates (db transactions, file writes)
2. **Business Logic**: Can you buy an item for $0? Can you access data ID+1?
3. **State Manipulation**: Can you skip a step in a multi-step flow?

#### C. Data Compromise Check
1. **Leakage**: Are PII, secrets, or internal IDs exposed in logs, error messages, or API responses?
2. **Integrity**: Can data be modified without authorization?
3. **Availability**: Can a payload cause a crash or high resource consumption (DoS)?

### Phase 4: Risk Assessment

#### Severity Classification

```text
CRITICAL (CVSS 9.0-10.0)
- Remote code execution
- Authentication bypass
- SQL injection in production endpoints
- Exposed secrets/credentials

HIGH (CVSS 7.0-8.9)
- Privilege escalation
- Sensitive data exposure
- XSS in authenticated areas
- Known exploits available

MEDIUM (CVSS 4.0-6.9)
- CSRF vulnerabilities
- Information disclosure
- Weak cryptography
- Outdated dependencies with patches available

LOW (CVSS 0.1-3.9)
- Minor information leaks
- Deprecated functions
- Code quality issues with security implications

INFO (CVSS 0.0)
- Security best practice recommendations
- Hardening opportunities
- Awareness items
```

#### Risk Factors
- **Exploitability**: How easy to exploit? (Automated, Simple, Complex, Theoretical)
- **Impact**: What's at risk? (Data breach, Service disruption, Financial loss)
- **Scope**: What's affected? (Single user, All users, System-wide)
- **Exposure**: Who can exploit? (Internet, Authenticated users, Admins only)

### Phase 5: Remediation Planning

#### Remediation Strategies
1. **Immediate Fixes** (Critical/High)
   - Version upgrades with compatibility verification
   - Code patches with security testing
   - Configuration hardening
   - Temporary mitigations (WAF rules, input validation)

2. **Scheduled Fixes** (Medium)
   - Plan for next sprint/release
   - Coordinate with feature development
   - Comprehensive testing required

3. **Long-term Improvements** (Low/Info)
   - Architectural refactoring
   - Security framework adoption
   - Developer training needs

#### Upgrade Guidance Template
```text
Package: [name]
  Current Version: [x.y.z]
  Vulnerable: YES
  CVE: [CVE-YYYY-NNNNN]
  Severity: [LEVEL]
  Fixed In: [a.b.c]
  Latest Stable: [p.q.r]
  Breaking Changes: [YES/NO]
  Migration Guide: [URL]
  Recommendation: Upgrade to [version] - [reason]
```

## Technology-Specific Security Patterns

For detailed vulnerability signatures and check patterns by language/framework, refer to the reference files in the plugin's `references/` directory. The following summaries indicate key focus areas per stack:

| Technology | Key Focus Areas |
|-----------|----------------|
| Node.js/JavaScript | Prototype pollution, RegEx DoS, dependency confusion, npm hijacking |
| Python | Pickle deserialization, SQL injection, SSTI, XML vulnerabilities |
| PHP | RCE, file inclusion, type juggling, deserialization |
| Go | SQL injection, command injection, race conditions, unsafe reflection |
| Java/Kotlin | Deserialization, XXE, SSRF, Spring vulnerabilities |
| .NET/C# | Deserialization, SQL injection, XSS, CSRF |
| Rust | Unsafe code blocks, memory safety, dependency vulnerabilities |
| React/Frontend | XSS, CSRF, sensitive data exposure, dependency vulnerabilities |
| React Native/Mobile | Insecure storage, weak crypto, API key exposure, deep linking |
| Vue.js | XSS via v-html, template injection, dependency vulnerabilities |
| NestJS | Injection attacks, authentication bypass, authorization flaws |
| Next.js | Server-side vulnerabilities, API route security, SSR/SSG security |

## Web Search Strategy for Vulnerability Intelligence

### Required Searches
For each dependency with suspected vulnerabilities, perform:
1. **CVE Search**: `"[package-name]" CVE [current-year] [previous-year]`
2. **Security Advisory**: `"[package-name]" security advisory vulnerability`
3. **Version Check**: `"[package-name]" latest stable version`
4. **Known Exploits**: `"[package-name]" exploit proof of concept`

### Trusted Sources
- NVD (nvd.nist.gov)
- Snyk Vulnerability Database
- GitHub Security Advisories
- npm/PyPI/Maven/NuGet security pages
- OWASP resources

## Output

**Output Location:** Write security report to `reports/security-analysis-[YYYYMMDD-HHMMSS].md`

### Security Report Structure
```markdown
# Security Analysis Report
Generated: [timestamp]
Project: [name]
Scan Scope: [files/dependencies scanned]
Scan Mode: [Full / Quick / Dependencies-Only]

## Executive Summary
- Total Vulnerabilities: [count]
- Critical: [count] | High: [count] | Medium: [count] | Low: [count]
- Immediate Action Required: [YES/NO]

## Critical Findings
[List of critical vulnerabilities requiring immediate attention]

## Detailed Analysis

### File-Level Vulnerabilities
[Per-file security issues with code snippets and line numbers]

### Dependency Vulnerabilities
[Per-package analysis with CVE details and upgrade paths]

### Context-Aware Risk Assessment
[Analysis of which vulnerabilities are actually exploitable in this codebase]

## Remediation Roadmap
### Immediate (0-24 hours)
[Critical fixes]

### Short-term (1-7 days)
[High priority fixes]

### Medium-term (1-4 weeks)
[Medium priority improvements]

### Long-term (1-3 months)
[Low priority and architectural improvements]

## Verification Steps
[How to test that fixes work correctly]

## References
[Links to CVE databases, security advisories, documentation]
```

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| No source files found | Empty directory or path doesn't exist | Verify the target path contains source code; check for typos |
| Project too large | Thousands of files causing timeouts | Use `--quick` for surface scan, or specify a subdirectory path to narrow scope |
| Audit tool not installed | `npm audit`, `pip-audit`, etc. not available | Report which tool is needed and provide installation command; fall back to web search for CVEs |
| Permission denied | Cannot read files in target directory | Report the inaccessible paths; suggest checking file permissions |
| No package manifest found | No package.json, requirements.txt, etc. | Skip dependency analysis; focus on static code analysis only |
| Network unavailable | Cannot reach CVE databases for web search | Use only local audit tools and static analysis; note that CVE verification was skipped |

## Best Practices
- Always verify vulnerability information from multiple sources
- Consider the specific context of the application
- Provide clear, actionable remediation steps
- Include code examples for fixes
- Link to official documentation
- Respect responsible disclosure practices
- Focus on practical, implementable solutions
