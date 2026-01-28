# Security Reference Guide

## Vulnerability Classification Framework

### OWASP Top 10 (2021)
1. **A01:2021 – Broken Access Control**
2. **A02:2021 – Cryptographic Failures**
3. **A03:2021 – Injection**
4. **A04:2021 – Insecure Design**
5. **A05:2021 – Security Misconfiguration**
6. **A06:2021 – Vulnerable and Outdated Components**
7. **A07:2021 – Identification and Authentication Failures**
8. **A08:2021 – Software and Data Integrity Failures**
9. **A09:2021 – Security Logging and Monitoring Failures**
10. **A10:2021 – Server-Side Request Forgery (SSRF)**

### CWE Top 25 Most Dangerous Software Weaknesses
1. CWE-787: Out-of-bounds Write
2. CWE-79: Cross-site Scripting (XSS)
3. CWE-89: SQL Injection
4. CWE-20: Improper Input Validation
5. CWE-125: Out-of-bounds Read
6. CWE-78: OS Command Injection
7. CWE-416: Use After Free
8. CWE-22: Path Traversal
9. CWE-352: CSRF
10. CWE-434: Unrestricted Upload of File with Dangerous Type

## CVSS Scoring Guide

### CVSS v3.1 Base Score Ranges
- **None**: 0.0
- **Low**: 0.1-3.9
- **Medium**: 4.0-6.9
- **High**: 7.0-8.9
- **Critical**: 9.0-10.0

### CVSS Metrics
**Base Metrics**:
- Attack Vector (AV): Network, Adjacent, Local, Physical
- Attack Complexity (AC): Low, High
- Privileges Required (PR): None, Low, High
- User Interaction (UI): None, Required
- Scope (S): Unchanged, Changed
- Confidentiality (C): None, Low, High
- Integrity (I): None, Low, High
- Availability (A): None, Low, High

## Vulnerability Database Sources

### Primary Sources
1. **National Vulnerability Database (NVD)**
   - URL: https://nvd.nist.gov/
   - Coverage: Comprehensive CVE database
   - Update Frequency: Daily

2. **Snyk Vulnerability Database**
   - URL: https://security.snyk.io/
   - Coverage: npm, PyPI, Maven, NuGet, RubyGems
   - Features: Detailed remediation advice

3. **GitHub Security Advisories**
   - URL: https://github.com/advisories
   - Coverage: GitHub-hosted projects
   - Features: Automated dependency alerts

4. **npm Security Advisories**
   - URL: https://www.npmjs.com/advisories
   - Coverage: npm packages
   - Integration: npm audit

5. **PyPI Advisory Database**
   - URL: https://github.com/pypa/advisory-database
   - Coverage: Python packages
   - Integration: pip-audit

### Language/Framework Specific
- **Node.js**: Node Security Platform, npm audit
- **Python**: PyUp Safety DB, pip-audit
- **Java**: Sonatype OSS Index, OWASP Dependency-Check
- **.NET**: NuGet vulnerability database
- **Ruby**: RubySec Advisory Database
- **PHP**: Packagist security advisories
- **Go**: Go vulnerability database
- **Rust**: RustSec Advisory Database

## Common Vulnerability Patterns by Language

### JavaScript/TypeScript
```javascript
// Prototype Pollution
Object.assign({}, userInput); // Vulnerable
Object.prototype.isAdmin = true; // Pollution

// Command Injection
exec(`ping ${userInput}`); // Vulnerable

// Path Traversal
readFile(`./uploads/${userInput}`); // Vulnerable

// ReDoS
/^(a+)+$/.test(userInput); // Vulnerable

// XSS
element.innerHTML = userInput; // Vulnerable
```

### Python
```python
# Code Injection
eval(user_input)  # Vulnerable
exec(user_input)  # Vulnerable

# SQL Injection
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # Vulnerable

# Pickle Deserialization
pickle.loads(user_input)  # Vulnerable

# SSTI
Template(user_input).render()  # Vulnerable

# Command Injection
os.system(f"ping {user_input}")  # Vulnerable
```

### PHP
```php
// Code Injection
eval($user_input);  // Vulnerable

// SQL Injection
mysqli_query("SELECT * FROM users WHERE id = " . $_GET['id']);  // Vulnerable

// File Inclusion
include($_GET['page'] . '.php');  // Vulnerable

// Deserialization
unserialize($user_input);  // Vulnerable

// Command Injection
shell_exec("ping " . $user_input);  // Vulnerable
```

### Java
```java
// Deserialization
ObjectInputStream ois = new ObjectInputStream(userInput);
Object obj = ois.readObject();  // Vulnerable

// SQL Injection
Statement stmt = conn.createStatement();
stmt.execute("SELECT * FROM users WHERE id = " + userId);  // Vulnerable

// XXE
DocumentBuilder db = factory.newDocumentBuilder();
db.parse(userInput);  // Vulnerable

// Path Traversal
new File(uploadDir + userInput);  // Vulnerable
```

## Secure Coding Patterns

### Input Validation
```typescript
// Whitelist approach (preferred)
const allowedChars = /^[a-zA-Z0-9_-]+$/;
if (!allowedChars.test(input)) {
  throw new Error('Invalid input');
}

// Type validation
if (typeof input !== 'string') {
  throw new Error('Invalid type');
}

// Length validation
if (input.length > 100) {
  throw new Error('Input too long');
}

// Schema validation (best)
const schema = Joi.object({
  username: Joi.string().alphanum().min(3).max(30).required(),
  email: Joi.string().email().required()
});
```

### Output Encoding
```javascript
// HTML encoding
function escapeHtml(unsafe) {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// URL encoding
const safe = encodeURIComponent(userInput);

// JavaScript encoding
const safe = JSON.stringify(userInput);
```

### Parameterized Queries
```sql
-- Vulnerable
SELECT * FROM users WHERE id = ${userId}

-- Secure (PostgreSQL)
SELECT * FROM users WHERE id = $1

-- Secure (MySQL)
SELECT * FROM users WHERE id = ?

-- Secure (Named parameters)
SELECT * FROM users WHERE id = :userId
```

### Secure Password Handling
```javascript
// Node.js with bcrypt
const bcrypt = require('bcrypt');
const saltRounds = 12;

// Hash
const hash = await bcrypt.hash(password, saltRounds);

// Verify
const match = await bcrypt.compare(password, hash);
```

```python
# Python with argon2
from argon2 import PasswordHasher

ph = PasswordHasher()

# Hash
hash = ph.hash(password)

# Verify
try:
    ph.verify(hash, password)
except:
    # Invalid password
    pass
```

### Secure Random Generation
```javascript
// Node.js
const crypto = require('crypto');
const token = crypto.randomBytes(32).toString('hex');

// Browser
const array = new Uint8Array(32);
crypto.getRandomValues(array);
```

```python
# Python
import secrets
token = secrets.token_urlsafe(32)
random_number = secrets.randbelow(100)
```

## Security Headers

### Essential Headers
```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

### Implementation (Express.js)
```javascript
const helmet = require('helmet');
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
    }
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
}));
```

## Dependency Security Tools

### Node.js
```bash
# npm audit
npm audit
npm audit fix
npm audit fix --force

# Snyk
npx snyk test
npx snyk monitor

# OWASP Dependency-Check
dependency-check --project myapp --scan .
```

### Python
```bash
# pip-audit
pip-audit

# Safety
safety check
safety check --json

# Bandit (SAST)
bandit -r .
```

### Java
```bash
# OWASP Dependency-Check
mvn org.owasp:dependency-check-maven:check

# Snyk
snyk test --all-projects
```

### .NET
```bash
# dotnet list package
dotnet list package --vulnerable

# OWASP Dependency-Check
dependency-check --project myapp --scan bin/
```

## Vulnerability Remediation Priority Matrix

| Severity | Exploitability | Exposure | Priority |
|----------|---------------|----------|----------|
| Critical | Easy | Public | P0 - Immediate |
| Critical | Easy | Internal | P0 - Immediate |
| Critical | Complex | Public | P1 - 24 hours |
| High | Easy | Public | P1 - 24 hours |
| High | Easy | Internal | P2 - 1 week |
| High | Complex | Public | P2 - 1 week |
| Medium | Easy | Public | P3 - 1 month |
| Medium | Any | Internal | P3 - 1 month |
| Low | Any | Any | P4 - Next sprint |

## Advanced Testing Tools & Techniques (Discovery)

### 1. Fuzzing Engines
*   **Python**: `Atheris` (Coverage-guided, libFuzzer based)
*   **Java**: `Jazzer` (Coverage-guided, libFuzzer based)
*   **Rust**: `cargo-fuzz` (libFuzzer), `FourFuzz` (Targeted unsafe)
*   **Go**: `Go Fuzzing` (Native since 1.18)
*   **Node.js**: `Jsfuzz` (Coverage-guided)

### 2. Taint Analysis Tools
*   **Concept**: Tracks data flow from source -> sink.
*   **Node.js**: `Augur`, `Snyk Code` (DeepCode engine)
*   **Python**: `PyT` (Python Taint), `Bandit` (Naive taint)
*   **Java**: `CodeQL` queries, `FindSecBugs`
*   **General**: `Semgrep` (Advanced ruleset)

### 3. Dynamic Analysis (DAST) Automation
*   **OWASP ZAP**: Automate via CI/CD (ZAP API).
*   **Burp Suite Enterprise**: Automated crawling and scanning.
*   **StackHawk**: DAST for developers (CI integrated).

### 4. Zero Tolerance Protocol Definition
**"Zero Tolerance"** means immediate build failure if:
*   **PII Leak**: Any regex match for SSN, Credit Card, or API Key in logs/output.
*   **Critical Injection**: Any unvalidated path from `request` to `exec`/`eval`/`sql`.
*   **Unsafe Config**: `DEBUG=True` in production config.
*   **Action**: These findings bypass "Risk Assessment" and are treated as blocking bugs.

## Web Search Query Templates

### CVE Search
```
"[package-name]" CVE [current-year]
"[package-name]" security vulnerability
site:nvd.nist.gov "[package-name]"
```

### Version Information
```
"[package-name]" latest version
"[package-name]" changelog security
"[package-name]" release notes
```

### Exploit Research
```
"[CVE-ID]" exploit
"[CVE-ID]" proof of concept
"[package-name]" "[vulnerability-type]" exploit
```

### Remediation
```
"[package-name]" security patch
"[CVE-ID]" fix
"[package-name]" upgrade guide
```

## Compliance Frameworks

### PCI DSS Requirements
- 6.5.1: Injection flaws
- 6.5.2: Buffer overflows
- 6.5.3: Insecure cryptographic storage
- 6.5.4: Insecure communications
- 6.5.5: Improper error handling
- 6.5.7: Cross-site scripting (XSS)
- 6.5.8: Improper access control
- 6.5.9: Cross-site request forgery (CSRF)
- 6.5.10: Broken authentication

### GDPR Security Requirements
- Article 32: Security of processing
- Article 33: Breach notification
- Article 34: Communication of breach to data subject
- Article 35: Data protection impact assessment

### SOC 2 Trust Principles
- Security
- Availability
- Processing Integrity
- Confidentiality
- Privacy

## References

### Standards
- OWASP: https://owasp.org/
- CWE: https://cwe.mitre.org/
- CVSS: https://www.first.org/cvss/
- NIST: https://www.nist.gov/

### Tools
- Snyk: https://snyk.io/
- Semgrep: https://semgrep.dev/
- SonarQube: https://www.sonarqube.org/
- Checkmarx: https://www.checkmarx.com/

### Learning Resources
- OWASP Cheat Sheets: https://cheatsheetseries.owasp.org/
- PortSwigger Web Security Academy: https://portswigger.net/web-security
- HackerOne Hacktivity: https://hackerone.com/hacktivity
