# Node.js / JavaScript Security Analysis

## Overview
Node.js applications face unique security challenges due to the dynamic nature of JavaScript, the vast npm ecosystem, and common architectural patterns. This guide provides deep security analysis patterns specific to Node.js.

## Critical Vulnerability Patterns

### 1. Prototype Pollution
**Risk**: Allows attackers to modify Object.prototype, affecting all objects
**Detection Patterns**:
```javascript
// VULNERABLE
function merge(target, source) {
  for (let key in source) {
    target[key] = source[key]; // No prototype check
  }
}

// VULNERABLE
_.merge(obj, userInput); // Lodash < 4.17.12
```

**Secure Alternative**:
```javascript
function merge(target, source) {
  for (let key in source) {
    if (Object.prototype.hasOwnProperty.call(source, key) && key !== '__proto__') {
      target[key] = source[key];
    }
  }
}
```

### 2. Command Injection
**Risk**: Arbitrary command execution on the server
**Detection Patterns**:
```javascript
// VULNERABLE
const { exec } = require('child_process');
exec(`ping ${userInput}`); // Direct interpolation

// VULNERABLE
exec('ls ' + userInput);
```

**Secure Alternative**:
```javascript
const { execFile } = require('child_process');
execFile('ping', [userInput]); // Use array arguments

// Or with validation
const { spawn } = require('child_process');
const sanitized = userInput.replace(/[^a-zA-Z0-9.-]/g, '');
spawn('ping', [sanitized]);
```

### 3. Path Traversal
**Risk**: Access to files outside intended directory
**Detection Patterns**:
```javascript
// VULNERABLE
const fs = require('fs');
app.get('/file', (req, res) => {
  fs.readFile(`./uploads/${req.query.filename}`, ...); // No validation
});

// VULNERABLE
const filePath = path.join(__dirname, 'uploads', userInput);
```

**Secure Alternative**:
```javascript
const path = require('path');
const fs = require('fs');

app.get('/file', (req, res) => {
  const filename = path.basename(req.query.filename); // Remove path components
  const filePath = path.join(__dirname, 'uploads', filename);
  
  // Verify the resolved path is within uploads directory
  if (!filePath.startsWith(path.join(__dirname, 'uploads'))) {
    return res.status(403).send('Access denied');
  }
  
  fs.readFile(filePath, ...);
});
```

### 4. SQL Injection
**Risk**: Database compromise, data theft
**Detection Patterns**:
```javascript
// VULNERABLE - String concatenation
db.query(`SELECT * FROM users WHERE id = ${req.params.id}`);

// VULNERABLE - Template literals
db.query(`SELECT * FROM users WHERE name = '${req.body.name}'`);

// VULNERABLE - Sequelize raw queries
sequelize.query(`SELECT * FROM users WHERE email = '${email}'`);
```

**Secure Alternative**:
```javascript
// Parameterized queries
db.query('SELECT * FROM users WHERE id = ?', [req.params.id]);

// Sequelize with replacements
sequelize.query('SELECT * FROM users WHERE email = :email', {
  replacements: { email: email },
  type: QueryTypes.SELECT
});

// ORM methods (preferred)
User.findOne({ where: { email: email } });
```

### 5. NoSQL Injection (MongoDB)
**Risk**: Authentication bypass, data exfiltration
**Detection Patterns**:
```javascript
// VULNERABLE
db.collection('users').findOne({ username: req.body.username });
// If req.body.username = { $ne: null }, returns first user

// VULNERABLE
User.find({ email: req.query.email }); // Mongoose without sanitization
```

**Secure Alternative**:
```javascript
// Validate input type
if (typeof req.body.username !== 'string') {
  return res.status(400).send('Invalid input');
}

// Use strict schema validation
const userSchema = new mongoose.Schema({
  username: { type: String, required: true },
  email: { type: String, required: true }
}, { strict: true });

// Sanitize with mongo-sanitize
const sanitize = require('mongo-sanitize');
const cleanUsername = sanitize(req.body.username);
```

### 6. Regular Expression Denial of Service (ReDoS)
**Risk**: Application hang/crash via crafted input
**Detection Patterns**:
```javascript
// VULNERABLE - Catastrophic backtracking
const emailRegex = /^([a-zA-Z0-9_\.-]+)@([\da-zA-Z\.-]+)\.([a-zA-Z\.]{2,6})$/;
const badRegex = /(a+)+$/; // Exponential time complexity
const evilRegex = /^(a|a)*$/;

if (badRegex.test(userInput)) { ... } // Can hang with "aaaaaaaaaaaaaaaaaaaaaaaaaaaa!"
```

**Secure Alternative**:
```javascript
// Use safe-regex to detect vulnerable patterns
const safeRegex = require('safe-regex');
if (!safeRegex(myRegex)) {
  console.warn('Potentially unsafe regex detected');
}

// Use simpler patterns
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Use validator libraries
const validator = require('validator');
if (validator.isEmail(userInput)) { ... }
```

### 7. JWT Vulnerabilities
**Risk**: Authentication bypass, privilege escalation
**Detection Patterns**:
```javascript
// VULNERABLE - Weak secret
jwt.sign(payload, 'secret');

// VULNERABLE - No algorithm verification
jwt.verify(token, secret); // Accepts "none" algorithm

// VULNERABLE - No expiration
jwt.sign(payload, secret); // Token valid forever
```

**Secure Alternative**:
```javascript
// Strong secret from environment
const secret = process.env.JWT_SECRET; // Min 256 bits

// Specify algorithm explicitly
jwt.verify(token, secret, { algorithms: ['HS256'] });

// Set expiration
jwt.sign(payload, secret, { 
  expiresIn: '1h',
  algorithm: 'HS256'
});

// Use RS256 for better security
jwt.sign(payload, privateKey, { algorithm: 'RS256', expiresIn: '1h' });
jwt.verify(token, publicKey, { algorithms: ['RS256'] });
```

### 8. Insecure Deserialization
**Risk**: Remote code execution
**Detection Patterns**:
```javascript
// VULNERABLE
const obj = eval('(' + userInput + ')'); // Never use eval

// VULNERABLE - node-serialize
const serialize = require('node-serialize');
const obj = serialize.unserialize(userInput); // Can execute code

// RISKY
const obj = JSON.parse(userInput); // Safe for JSON, but validate structure
```

**Secure Alternative**:
```javascript
// Use JSON.parse with validation
try {
  const obj = JSON.parse(userInput);
  
  // Validate structure
  if (typeof obj.name !== 'string' || typeof obj.age !== 'number') {
    throw new Error('Invalid structure');
  }
} catch (e) {
  return res.status(400).send('Invalid JSON');
}

// Use schema validation
const Joi = require('joi');
const schema = Joi.object({
  name: Joi.string().required(),
  age: Joi.number().integer().min(0).required()
});

const { error, value } = schema.validate(JSON.parse(userInput));
```

## Dependency-Specific Vulnerabilities

### Express.js Security
**Required Middleware**:
```javascript
const helmet = require('helmet'); // Security headers
const rateLimit = require('express-rate-limit'); // Rate limiting
const mongoSanitize = require('express-mongo-sanitize'); // NoSQL injection prevention
const xss = require('xss-clean'); // XSS prevention

app.use(helmet());
app.use(express.json({ limit: '10kb' })); // Body size limit
app.use(mongoSanitize());
app.use(xss());

const limiter = rateLimit({
  max: 100,
  windowMs: 60 * 60 * 1000,
  message: 'Too many requests'
});
app.use('/api', limiter);
```

### Common Vulnerable Packages
**Check for these and search for CVEs**:
- `lodash` < 4.17.21 (Prototype pollution)
- `axios` < 0.21.1 (SSRF)
- `express` < 4.17.3 (Various)
- `jsonwebtoken` < 9.0.0 (Algorithm confusion)
- `mongoose` < 5.13.15 (Query injection)
- `multer` < 1.4.4 (Path traversal)
- `node-forge` < 1.3.0 (Signature verification bypass)
- `ws` < 7.4.6 (ReDoS)

## Security Checklist

### Authentication \u0026 Authorization
- [ ] Passwords hashed with bcrypt (cost factor ≥ 12)
- [ ] JWT tokens have expiration
- [ ] Refresh token rotation implemented
- [ ] Rate limiting on auth endpoints
- [ ] Account lockout after failed attempts
- [ ] Secure session configuration

### Input Validation
- [ ] All user input validated and sanitized
- [ ] File upload restrictions (type, size)
- [ ] SQL/NoSQL injection prevention
- [ ] XSS prevention in all outputs
- [ ] CSRF tokens on state-changing operations

### Cryptography
- [ ] No hardcoded secrets
- [ ] Secrets in environment variables
- [ ] Use crypto.randomBytes() for random values
- [ ] TLS/HTTPS enforced
- [ ] Strong cipher suites configured

### Dependencies
- [ ] Run `npm audit` regularly
- [ ] Keep dependencies updated
- [ ] Use `npm ci` in production
- [ ] Lock file committed
- [ ] Review dependency licenses

### Error Handling
- [ ] No stack traces in production
- [ ] Generic error messages to users
- [ ] Detailed logging server-side
- [ ] Sensitive data not logged

### Configuration
- [ ] NODE_ENV=production in production
- [ ] Debug mode disabled
- [ ] Unnecessary services disabled
- [ ] Security headers configured (helmet.js)

## Advanced Security Testing Techniques (Discovery Focus)

### 1. Advanced Prototype Pollution Discovery
**Methodology**: Move beyond static checking (e.g., `hasOwnProperty`). Actively fuzz for gadget chains.
*   **Technique**: Use `UOPF` (Undefined-oriented Programming Framework) or manual property injection.
*   **Fuzzing Payloads**:
    ```json
    {"__proto__": {"polluted": true}}
    {"constructor": {"prototype": {"polluted": true}}}
    {"__proto__": {"isAdmin": true}}
    ```
*   **Verification**: Check if `({}).polluted === true` in the application console or response.

### 2. Taint Analysis for Injection Vectors
**Methodology**: Trace data from source to sink.
*   **Tools**: Use `Augur` or instrumented tests to mark inputs as "tainted".
*   **Deep Sink Analysis**:
    *   **SQL/NoSQL**: Does `req.body.id` reach `db.query`?
    *   **Command**: Does `req.query.file` reach `child_process.exec`?
    *   **Code**: Does `req.params.code` reach `eval` or `new Function`?
*   **Manual Trace**: Grep for `exec(`, `eval(`, `query(` and backtrace variables to `req` object.

### 3. ReDoS Fuzzing
**Methodology**: Identify regexes with exponential complexity.
*   **Discovery**: Extract all regexes from source.
*   **Analysis**: Test against strings like `aaaaaaaaaaaaaaaaaaaaaaaaaaaa!` (30+ chars).
*   **Tool**: Use `safe-regex` linter plugin or online ReDoS checkers.

### 4. Supply Chain & Malicious Package Detection
**Methodology**: Assume `npm audit` misses 0-days.
*   **Behavioral Analysis**: Check `node_modules` for minified code or encoded strings in unlikely places.
*   **Network Monitoring**: Does a simple utility package make network requests?
*   **Lockfile Analysis**: Check `package-lock.json` for registry URLs that are not `registry.npmjs.org`.

### 5. Zero Tolerance Data Compromise Protocol
**Mandate**: If ANY checking reveals exposure of PII, secrets, or raw internal errors:
1.  **Stop**: Do not proceed with deployment.
2.  **Audit**: Identify the exact line logging the object.
3.  **Remediate**: Apply field-masking (e.g., `winston-masker`) on the logger.
4.  **Verify**: Re-run the specific compromised test case.

## Web Search Queries for Node.js Vulnerabilities
```
"[package-name]" npm security vulnerability CVE
"[package-name]" github security advisory
"node.js" "[vulnerability-type]" exploit
"express" security best practices 2024
npm audit [package-name]
```

## References
- [Node.js Security Best Practices](https://nodejs.org/en/docs/guides/security/)
- [OWASP Node.js Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Nodejs_Security_Cheat_Sheet.html)
- [npm Security Advisories](https://www.npmjs.com/advisories)
- [Snyk Vulnerability Database](https://security.snyk.io/)
