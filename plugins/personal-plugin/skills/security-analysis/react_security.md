# React / Frontend Security Analysis

## Overview
React applications face unique security challenges including XSS, CSRF, sensitive data exposure, and dependency vulnerabilities. This guide provides comprehensive security patterns for React and frontend applications.

## Critical Vulnerability Patterns

### 1. Cross-Site Scripting (XSS)
**Risk**: Code execution in user's browser, session hijacking
**Detection Patterns**:
```jsx
// VULNERABLE - dangerouslySetInnerHTML
function UserComment({ comment }) {
  return <div dangerouslySetInnerHTML={{ __html: comment }} />;
}

// VULNERABLE - Direct DOM manipulation
function Component() {
  useEffect(() => {
    document.getElementById('output').innerHTML = userInput;
  }, []);
}

// VULNERABLE - href with javascript:
<a href={`javascript:${userInput}`}>Click</a>

// VULNERABLE - Unescaped user input in attributes
<div title={userInput}></div> // Can break out with quotes
```

**Secure Alternative**:
```jsx
// React auto-escapes by default
function UserComment({ comment }) {
  return <div>{comment}</div>; // Safe
}

// Use DOMPurify for HTML sanitization
import DOMPurify from 'dompurify';

function SafeHTML({ html }) {
  const clean = DOMPurify.sanitize(html);
  return <div dangerouslySetInnerHTML={{ __html: clean }} />;
}

// Validate URLs
function SafeLink({ url, children }) {
  const isValidUrl = url.startsWith('http://') || url.startsWith('https://');
  return isValidUrl ? <a href={url}>{children}</a> : <span>{children}</span>;
}
```

### 2. Sensitive Data Exposure
**Risk**: API keys, tokens, PII exposed in frontend code
**Detection Patterns**:
```javascript
// VULNERABLE - API keys in code
const API_KEY = 'sk_live_abc123xyz';
fetch(`https://api.example.com?key=${API_KEY}`);

// VULNERABLE - Secrets in localStorage
localStorage.setItem('apiKey', 'secret-key-123');

// VULNERABLE - Sensitive data in Redux store visible in DevTools
const initialState = {
  user: {
    ssn: '123-45-6789',
    creditCard: '4111-1111-1111-1111'
  }
};

// VULNERABLE - Exposing all env vars
console.log(process.env); // Logs all environment variables
```

**Secure Alternative**:
```javascript
// Use backend proxy for API calls
fetch('/api/proxy/endpoint'); // Backend adds API key

// Never store sensitive data in localStorage
// Use httpOnly cookies for tokens
// Set via backend: Set-Cookie: token=...; HttpOnly; Secure; SameSite=Strict

// Don't store sensitive data in frontend state
const initialState = {
  user: {
    id: '123',
    name: 'John Doe'
    // No SSN, credit card, etc.
  }
};

// Only expose REACT_APP_ prefixed vars
const apiUrl = process.env.REACT_APP_API_URL; // Safe pattern
```

### 3. Insecure Authentication Token Storage
**Risk**: Token theft via XSS
**Detection Patterns**:
```javascript
// VULNERABLE - Token in localStorage
localStorage.setItem('authToken', token);
const token = localStorage.getItem('authToken');

// VULNERABLE - Token in sessionStorage
sessionStorage.setItem('jwt', token);

// VULNERABLE - Token in Redux state accessible to XSS
const authSlice = createSlice({
  name: 'auth',
  initialState: { token: null }
});
```

**Secure Alternative**:
```javascript
// Use httpOnly cookies (set by backend)
// Backend: res.cookie('token', jwt, { 
//   httpOnly: true, 
//   secure: true, 
//   sameSite: 'strict' 
// });

// Frontend: Cookies sent automatically
fetch('/api/protected', {
  credentials: 'include' // Include cookies
});

// If localStorage is necessary, encrypt sensitive data
import CryptoJS from 'crypto-js';

const encryptedToken = CryptoJS.AES.encrypt(
  token, 
  userPassword
).toString();
localStorage.setItem('token', encryptedToken);
```

### 4. CSRF Vulnerabilities
**Risk**: Unauthorized actions on behalf of authenticated users
**Detection Patterns**:
```javascript
// VULNERABLE - State-changing GET requests
<a href="/api/delete-account">Delete Account</a>

// VULNERABLE - No CSRF token on forms
fetch('/api/transfer', {
  method: 'POST',
  body: JSON.stringify({ amount: 1000 })
});

// VULNERABLE - CORS misconfiguration
// Backend: app.use(cors({ origin: '*' }));
```

**Secure Alternative**:
```javascript
// Use POST/PUT/DELETE for state changes
const handleDelete = async () => {
  await fetch('/api/delete-account', { method: 'DELETE' });
};

// Include CSRF token
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
fetch('/api/transfer', {
  method: 'POST',
  headers: {
    'X-CSRF-Token': csrfToken
  },
  body: JSON.stringify({ amount: 1000 })
});

// Proper CORS configuration (backend)
// app.use(cors({ 
//   origin: 'https://yourdomain.com',
//   credentials: true 
// }));

// Use SameSite cookies
// Set-Cookie: token=...; SameSite=Strict
```

### 5. Dependency Vulnerabilities
**Risk**: Known vulnerabilities in npm packages
**Detection Patterns**:
```json
// package.json with outdated packages
{
  "dependencies": {
    "react": "16.8.0",  // Old version
    "axios": "0.18.0",  // Known vulnerabilities
    "lodash": "4.17.15" // Prototype pollution
  }
}
```

**Secure Alternative**:
```bash
# Regular audits
npm audit
npm audit fix

# Use npm-check-updates
npx npm-check-updates -u
npm install

# Lock dependencies
npm ci  # Use in CI/CD

# Check specific package
npm audit --package=axios
```

### 6. Insecure Direct Object References (IDOR)
**Risk**: Unauthorized access to resources
**Detection Patterns**:
```javascript
// VULNERABLE - Client-side authorization
function DeleteButton({ userId }) {
  const currentUser = useSelector(state => state.user);
  
  const handleDelete = () => {
    // Client-side check only
    if (currentUser.id === userId) {
      fetch(`/api/users/${userId}`, { method: 'DELETE' });
    }
  };
  
  return <button onClick={handleDelete}>Delete</button>;
}

// VULNERABLE - Predictable IDs in URLs
<Link to={`/profile/${userId}`}>View Profile</Link>
```

**Secure Alternative**:
```javascript
// Server-side authorization is mandatory
function DeleteButton({ userId }) {
  const handleDelete = async () => {
    try {
      // Backend verifies user has permission
      await fetch(`/api/users/${userId}`, { method: 'DELETE' });
    } catch (error) {
      if (error.status === 403) {
        alert('Unauthorized');
      }
    }
  };
  
  return <button onClick={handleDelete}>Delete</button>;
}

// Use UUIDs instead of sequential IDs
<Link to={`/profile/${userUuid}`}>View Profile</Link>
```

### 7. Insecure File Uploads
**Risk**: Malicious file execution, XSS
**Detection Patterns**:
```javascript
// VULNERABLE - No file type validation
function FileUpload() {
  const handleUpload = (e) => {
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append('file', file);
    fetch('/api/upload', { method: 'POST', body: formData });
  };
  
  return <input type="file" onChange={handleUpload} />;
}

// VULNERABLE - Client-side validation only
const allowedTypes = ['image/jpeg', 'image/png'];
if (!allowedTypes.includes(file.type)) {
  return; // Can be bypassed
}
```

**Secure Alternative**:
```javascript
function SecureFileUpload() {
  const [error, setError] = useState('');
  
  const handleUpload = async (e) => {
    const file = e.target.files[0];
    
    // Client-side validation (UX only)
    const allowedTypes = ['image/jpeg', 'image/png'];
    const maxSize = 5 * 1024 * 1024; // 5MB
    
    if (!allowedTypes.includes(file.type)) {
      setError('Invalid file type');
      return;
    }
    
    if (file.size > maxSize) {
      setError('File too large');
      return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      // Backend performs real validation
      await fetch('/api/upload', { 
        method: 'POST', 
        body: formData 
      });
    } catch (err) {
      setError('Upload failed');
    }
  };
  
  return (
    <>
      <input 
        type="file" 
        accept="image/jpeg,image/png"
        onChange={handleUpload} 
      />
      {error && <p>{error}</p>}
    </>
  );
}
```

### 8. Postmessage Vulnerabilities
**Risk**: XSS, data leakage
**Detection Patterns**:
```javascript
// VULNERABLE - No origin validation
window.addEventListener('message', (event) => {
  document.getElementById('output').innerHTML = event.data;
});

// VULNERABLE - Accepting messages from any origin
window.parent.postMessage(sensitiveData, '*');
```

**Secure Alternative**:
```javascript
// Validate origin
window.addEventListener('message', (event) => {
  // Verify origin
  if (event.origin !== 'https://trusted-domain.com') {
    return;
  }
  
  // Validate data structure
  if (typeof event.data !== 'object' || !event.data.type) {
    return;
  }
  
  // Sanitize before using
  const sanitized = DOMPurify.sanitize(event.data.content);
  document.getElementById('output').textContent = sanitized;
});

// Specify target origin
window.parent.postMessage(data, 'https://trusted-domain.com');
```

## React-Specific Security Best Practices

### Content Security Policy (CSP)
```html
<!-- In index.html -->
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline' 'unsafe-eval'; 
               style-src 'self' 'unsafe-inline'; 
               img-src 'self' data: https:; 
               font-src 'self' data:; 
               connect-src 'self' https://api.yourdomain.com;">
```

### Security Headers (via backend)
```javascript
// Express.js example
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

### Secure State Management
```javascript
// Don't store sensitive data in Redux
const userSlice = createSlice({
  name: 'user',
  initialState: {
    id: null,
    name: null,
    email: null,
    // ❌ Don't store: password, SSN, credit cards, tokens
  }
});

// Use React Context for sensitive operations
const AuthContext = createContext();

function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  // Token stored in httpOnly cookie, not in state
  const login = async (credentials) => {
    await fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
      credentials: 'include' // Send cookies
    });
    setIsAuthenticated(true);
  };
  
  return (
    <AuthContext.Provider value={{ isAuthenticated, login }}>
      {children}
    </AuthContext.Provider>
  );
}
```

## Common Vulnerable Packages
**Check for CVEs**:
- `react-scripts` < 5.0.1 (Various)
- `axios` < 1.6.0 (SSRF)
- `lodash` < 4.17.21 (Prototype pollution)
- `moment` (Deprecated, use date-fns or dayjs)
- `node-forge` < 1.3.0 (Signature verification)
- `minimist` < 1.2.6 (Prototype pollution)
- `nth-check` < 2.0.1 (ReDoS)

## Security Checklist

### Input/Output
- [ ] XSS prevention (avoid dangerouslySetInnerHTML)
- [ ] Sanitize HTML with DOMPurify when needed
- [ ] Validate URLs before using in href
- [ ] Use textContent instead of innerHTML

### Authentication
- [ ] Tokens in httpOnly cookies
- [ ] CSRF protection implemented
- [ ] Secure session management
- [ ] Logout clears all auth data

### Data Protection
- [ ] No API keys in frontend code
- [ ] Sensitive data not in localStorage
- [ ] HTTPS enforced
- [ ] Secure communication with backend

### Dependencies
- [ ] Run npm audit regularly
- [ ] Keep dependencies updated
- [ ] Review package permissions
- [ ] Use lock files (package-lock.json)

### Configuration
- [ ] CSP headers configured
- [ ] Security headers (via helmet.js on backend)
- [ ] CORS properly configured
- [ ] Error boundaries don't leak info

## Advanced Frontend Discovery (Discovery Focus)

### 1. Component Fuzzing (Props Injection)
**Methodology**: Inject malicious payloads into component props to test rendering safety.
*   **Technique**: Use `react-fuzz` or custom tests.
*   **Payloads**:
    *   `<img src=x onerror=alert(1)>`
    *   `javascript:alert(1)`
    *   `{{constructor.constructor('alert(1)')()}}` (Template injection)
*   **Action**: Render components with these props and check for execution.

### 2. State Manipulation Testing
**Methodology**: Can a user modify application state to bypass checks?
*   **Technique**: Use Redux DevTools or standard JS console.
*   **Action**:
    1.  Open Console: `window.store.dispatch({type: 'LOGIN_SUCCESS', payload: {isAdmin: true}})`
    2.  Modify Context: React DevTools -> Components -> Select Provider -> Edit value.
    3.  **Zero Tolerance**: If client-side state modification allows admin action without server verification, flag as **CRITICAL**.

### 3. CSP Bypass Testing
**Methodology**: Verify if Content Security Policy is actually effective.
*   **Technique**: Attempt to inject inline scripts or load external resources.
*   **Action**:
    1.  Inject `<script>alert(1)</script>` via DevTools.
    2.  Check if it executes (should be blocked).
    3.  Check Network tab for reports sent to `report-uri`.
    4.  Verify `script-src` does not contain `unsafe-inline` or wildcards `*`.

### 4. Zero Tolerance Data Compromise Protocol
**Mandate**: Check browser storage and logs for sensitive data.
*   **Audit**:
    1.  `localStorage.getItem('token')` -> **FAIL** if plain JWT.
    2.  `sessionStorage` -> Check for PII.
    3.  `document.cookie` -> Check keys sans `HttpOnly`.
    4.  **Remediate**: Move all auth tokens to `HttpOnly` Set-Cookie headers.

## Web Search Queries
```
"[package-name]" npm CVE vulnerability
"react" XSS vulnerability prevention
"[package-name]" security advisory github
npm audit [package-name]
"react security best practices" 2024
```

## References
- [React Security Best Practices](https://react.dev/learn/security)
- [OWASP Frontend Security](https://owasp.org/www-project-web-security-testing-guide/)
- [npm Security Advisories](https://www.npmjs.com/advisories)
