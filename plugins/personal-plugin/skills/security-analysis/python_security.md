# Python Security Analysis

## Overview
Python applications face security challenges from dynamic typing, powerful built-in functions, serialization vulnerabilities, and framework-specific issues. This guide provides comprehensive security analysis patterns for Python.

## Critical Vulnerability Patterns

### 1. Code Injection via eval/exec
**Risk**: Arbitrary code execution
**Detection Patterns**:
```python
# VULNERABLE
user_input = request.GET.get('code')
eval(user_input)  # Never use with user input

# VULNERABLE
exec(user_input)

# VULNERABLE
compile(user_input, '<string>', 'exec')

# VULNERABLE
__import__(user_input)
```

**Secure Alternative**:
```python
# Use ast.literal_eval for safe evaluation of literals
import ast
try:
    value = ast.literal_eval(user_input)  # Only evaluates literals
except (ValueError, SyntaxError):
    raise ValueError("Invalid input")

# For math expressions, use a safe evaluator
from simpleeval import simple_eval
result = simple_eval(user_input, names={"x": 10})

# Better: Use structured data formats
import json
data = json.loads(user_input)
```

### 2. SQL Injection
**Risk**: Database compromise, data theft
**Detection Patterns**:
```python
# VULNERABLE - String formatting
cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)

# VULNERABLE - f-strings
cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")

# VULNERABLE - String concatenation
query = "SELECT * FROM users WHERE email = '" + email + "'"
cursor.execute(query)

# VULNERABLE - Django raw queries
User.objects.raw(f"SELECT * FROM users WHERE id = {user_id}")
```

**Secure Alternative**:
```python
# Parameterized queries (psycopg2)
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# SQLAlchemy ORM
user = session.query(User).filter(User.id == user_id).first()

# Django ORM
user = User.objects.filter(id=user_id).first()

# Django raw queries with parameters
User.objects.raw("SELECT * FROM users WHERE id = %s", [user_id])
```

### 3. Unsafe Deserialization (Pickle)
**Risk**: Remote code execution
**Detection Patterns**:
```python
# VULNERABLE
import pickle
data = pickle.loads(user_input)  # Can execute arbitrary code

# VULNERABLE
import yaml
data = yaml.load(user_input)  # Use yaml.safe_load instead

# VULNERABLE
import marshal
code = marshal.loads(user_input)
```

**Secure Alternative**:
```python
# Use JSON instead of pickle
import json
data = json.loads(user_input)

# If YAML is needed, use safe_load
import yaml
data = yaml.safe_load(user_input)

# For complex objects, use structured formats
from dataclasses import dataclass, asdict
import json

@dataclass
class User:
    name: str
    age: int

# Serialize
json_data = json.dumps(asdict(user))

# Deserialize with validation
data = json.loads(json_data)
user = User(**data)
```

### 4. Server-Side Template Injection (SSTI)
**Risk**: Remote code execution
**Detection Patterns**:
```python
# VULNERABLE - Jinja2
from jinja2 import Template
template = Template(user_input)  # User controls template
output = template.render()

# VULNERABLE - Django
from django.template import Template
t = Template(user_input)

# VULNERABLE - String formatting as template
template = "Hello, %s" % user_input  # Can be exploited
```

**Secure Alternative**:
```python
# Use sandboxed environment
from jinja2.sandbox import SandboxedEnvironment
env = SandboxedEnvironment()
template = env.from_string(user_input)

# Better: Don't allow user-controlled templates
template = env.get_template('safe_template.html')
output = template.render(name=user_input)  # Only data is user-controlled

# Django - use template from file
from django.template.loader import render_to_string
output = render_to_string('template.html', {'name': user_input})
```

### 5. Command Injection
**Risk**: Arbitrary command execution
**Detection Patterns**:
```python
# VULNERABLE
import os
os.system(f"ping {user_input}")

# VULNERABLE
os.popen(f"ls {directory}")

# VULNERABLE - subprocess with shell=True
import subprocess
subprocess.call(f"ping {user_input}", shell=True)

# VULNERABLE
subprocess.Popen("echo " + user_input, shell=True)
```

**Secure Alternative**:
```python
import subprocess
import shlex

# Use list arguments without shell=True
subprocess.run(["ping", "-c", "1", user_input], check=True)

# If shell is needed, use shlex.quote
safe_input = shlex.quote(user_input)
subprocess.run(f"ping -c 1 {safe_input}", shell=True)

# Better: Validate input first
import re
if not re.match(r'^[a-zA-Z0-9.-]+$', user_input):
    raise ValueError("Invalid input")
subprocess.run(["ping", "-c", "1", user_input])
```

### 6. Path Traversal
**Risk**: Unauthorized file access
**Detection Patterns**:
```python
# VULNERABLE
filename = request.GET.get('file')
with open(f'/uploads/{filename}', 'r') as f:
    content = f.read()

# VULNERABLE
import os
file_path = os.path.join('/uploads', user_input)
with open(file_path) as f:
    pass
```

**Secure Alternative**:
```python
import os
from pathlib import Path

# Validate and sanitize
def safe_join(directory, filename):
    # Remove path components
    filename = os.path.basename(filename)
    filepath = os.path.join(directory, filename)
    
    # Resolve to absolute path
    filepath = os.path.abspath(filepath)
    directory = os.path.abspath(directory)
    
    # Ensure file is within directory
    if not filepath.startswith(directory):
        raise ValueError("Invalid file path")
    
    return filepath

# Usage
safe_path = safe_join('/uploads', user_input)
with open(safe_path, 'r') as f:
    content = f.read()

# Or use pathlib
base_dir = Path('/uploads').resolve()
file_path = (base_dir / user_input).resolve()
if not file_path.is_relative_to(base_dir):
    raise ValueError("Invalid file path")
```

### 7. XML External Entity (XXE) Injection
**Risk**: File disclosure, SSRF, DoS
**Detection Patterns**:
```python
# VULNERABLE
import xml.etree.ElementTree as ET
tree = ET.parse(user_file)  # Default parser is vulnerable

# VULNERABLE
from lxml import etree
parser = etree.XMLParser()
tree = etree.parse(user_file, parser)

# VULNERABLE
import xml.dom.minidom
dom = xml.dom.minidom.parse(user_file)
```

**Secure Alternative**:
```python
# Use defusedxml
from defusedxml import ElementTree as ET
tree = ET.parse(user_file)

# Or configure parser securely
import xml.etree.ElementTree as ET
# Disable DTD processing
ET.XMLParser(resolve_entities=False)

# lxml secure configuration
from lxml import etree
parser = etree.XMLParser(
    resolve_entities=False,
    no_network=True,
    dtd_validation=False
)
tree = etree.parse(user_file, parser)
```

### 8. Weak Cryptography
**Risk**: Data exposure, authentication bypass
**Detection Patterns**:
```python
# VULNERABLE - MD5/SHA1 for passwords
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()
password_hash = hashlib.sha1(password.encode()).hexdigest()

# VULNERABLE - Weak random
import random
token = random.randint(1000, 9999)  # Predictable

# VULNERABLE - ECB mode
from Crypto.Cipher import AES
cipher = AES.new(key, AES.MODE_ECB)

# VULNERABLE - Hardcoded secrets
SECRET_KEY = "hardcoded-secret-key-123"
```

**Secure Alternative**:
```python
# Use bcrypt/argon2 for passwords
import bcrypt
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# Or use argon2 (recommended)
from argon2 import PasswordHasher
ph = PasswordHasher()
password_hash = ph.hash(password)

# Secure random
import secrets
token = secrets.token_urlsafe(32)
random_number = secrets.randbelow(10000)

# Secure encryption
from cryptography.fernet import Fernet
key = Fernet.generate_key()
cipher = Fernet(key)
encrypted = cipher.encrypt(data)

# Load secrets from environment
import os
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY not set")
```

## Framework-Specific Security

### Django Security
**Common Vulnerabilities**:
```python
# VULNERABLE - Disabled CSRF
@csrf_exempt
def my_view(request):
    pass

# VULNERABLE - SQL injection in raw queries
User.objects.raw(f"SELECT * FROM users WHERE id = {user_id}")

# VULNERABLE - XSS with safe filter
{{ user_input|safe }}  # In template

# VULNERABLE - Insecure deserialization
import pickle
data = pickle.loads(request.body)
```

**Secure Practices**:
```python
# Enable CSRF protection (default)
MIDDLEWARE = [
    'django.middleware.csrf.CsrfViewMiddleware',
]

# Use ORM
user = User.objects.get(id=user_id)

# Auto-escape templates (default)
{{ user_input }}  # Automatically escaped

# Secure settings
DEBUG = False  # In production
ALLOWED_HOSTS = ['yourdomain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

### Flask Security
**Common Vulnerabilities**:
```python
# VULNERABLE - No CSRF protection
@app.route('/transfer', methods=['POST'])
def transfer():
    amount = request.form['amount']
    # Process transfer

# VULNERABLE - Debug mode in production
app.run(debug=True)

# VULNERABLE - Insecure session secret
app.secret_key = 'dev'

# VULNERABLE - SSTI
return render_template_string(user_input)
```

**Secure Practices**:
```python
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman

app = Flask(__name__)
csrf = CSRFProtect(app)
Talisman(app)  # Security headers

# Secure configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Use templates from files
return render_template('template.html', data=user_input)

# Production
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
```

### FastAPI Security
**Secure Practices**:
```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, validator

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Input validation with Pydantic
class User(BaseModel):
    username: str
    email: str
    age: int
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email')
        return v

# Dependency injection for auth
async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401)
    return user

@app.post("/items/")
async def create_item(
    item: Item,
    current_user: User = Depends(get_current_user)
):
    # Automatically validated and authenticated
    pass
```

## Common Vulnerable Packages
**Check for CVEs**:
- `Django` < 4.2.8 (Various)
- `Flask` < 3.0.0 (Various)
- `requests` < 2.31.0 (Proxy authentication)
- `Pillow` < 10.0.1 (DoS, arbitrary code execution)
- `cryptography` < 41.0.6 (NULL pointer dereference)
- `PyYAML` < 6.0.1 (Arbitrary code execution)
- `Jinja2` < 3.1.3 (XSS)
- `SQLAlchemy` < 2.0.23 (SQL injection in specific cases)

## Security Checklist

### Input Validation
- [ ] All user input validated with Pydantic/Marshmallow
- [ ] SQL injection prevention (ORM or parameterized queries)
- [ ] Command injection prevention
- [ ] Path traversal prevention
- [ ] XSS prevention (template auto-escaping)

### Authentication \u0026 Authorization
- [ ] Passwords hashed with bcrypt/argon2
- [ ] Secure session configuration
- [ ] CSRF protection enabled
- [ ] Rate limiting on auth endpoints
- [ ] JWT tokens with expiration

### Cryptography
- [ ] No hardcoded secrets
- [ ] Secrets in environment variables
- [ ] Use secrets module for random values
- [ ] Strong encryption algorithms
- [ ] TLS/HTTPS enforced

### Dependencies
- [ ] Run `pip-audit` or `safety check` regularly
- [ ] Keep dependencies updated
- [ ] Use virtual environments
- [ ] Pin dependency versions
- [ ] Review dependency licenses

### Configuration
- [ ] DEBUG = False in production
- [ ] Secure cookie settings
- [ ] Security headers configured
- [ ] Error messages don't leak info
- [ ] Logging configured properly

## Advanced Python Security Discovery (Discovery Focus)

### 1. Fuzzing with Atheris (Google)
**Methodology**: Coverage-guided fuzzing to find unexpected crashes/exceptions.
*   **Technique**: Use `atheris` (libFuzzer for Python).
*   **Action**: Create a fuzz harness for critical parsers (XML, JSON, custom formats).
    ```python
    import atheris
    import sys
    
    def TestOneInput(data):
        try:
            my_risky_parser(data)
        except ValueError:
            pass # Expected
        except Exception:
            raise # Unexpected crash -> Vulnerability
            
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()
    ```

### 2. SSTI Payload Discovery
**Methodology**: Detect if user input is evaluated as a template.
*   **Technique**: Inject mathematical payloads into all string fields.
*   **Payloads**:
    *   `{{7*7}}` -> `49` (Jinja2)
    *   `${7*7}` -> `49` (Mako)
    *   `{{config}}` -> Dumps Flask configuration
    *   `{{request.application.__globals__.__builtins__.__import__('os').popen('id').read()}}` (RCE)
*   **Action**: Grep codebase for `render_template_string` (Flask) or `Template(` (Django/Jinja2).

### 3. Deserialization Gadget Discovery
**Methodology**: Assume `pickle` is being used safely, check for transitive unsafe usage.
*   **Audit**:
    1.  Search for `pickle.load` or `dill.load`.
    2.  Trace the input variable back to `request.body` or `redis`.
    3.  **Zero Tolerance**: If unauthenticated input reaches `pickle.load`, flag as **CRITICAL RCE**.

### 4. Zero Tolerance Data Compromise Protocol
**Mandate**: Inspect logs and database for unintentional leakage.
*   **Checks**:
    1.  **Sentry/Logs**: Search logs for "password", "token", "ssn".
    2.  **Django Debug Toolbar**: Ensure it's STRIPPED in production builds (check `requirements.txt`).
    3.  **Exception Leaks**: Trigger 500 errors and check if stack traces are returned to the client.

## Web Search Queries
```
"[package-name]" python CVE security vulnerability
"[package-name]" pypi security advisory
"python" "[vulnerability-type]" exploit
"Django" security best practices 2024
pip-audit [package-name]
```

## References
- [OWASP Python Security](https://owasp.org/www-project-python-security/)
- [Django Security](https://docs.djangoproject.com/en/stable/topics/security/)
- [Flask Security](https://flask.palletsprojects.com/en/latest/security/)
- [PyPI Security Advisories](https://pypi.org/security/)
