# PHP Security Analysis

## Overview
PHP applications face unique security challenges due to the language's permissive nature, legacy functions, and common misconfigurations. This guide provides comprehensive security analysis patterns for PHP.

## Dependency Scanning Commands

### Composer Audit
```bash
# Check for known vulnerabilities
composer audit

# Check for outdated packages
composer outdated

# Update with security fixes
composer update --with-dependencies
```

## Critical Vulnerability Patterns

### 1. Remote Code Execution (RCE)
**Risk**: Arbitrary code execution on server
**Detection Patterns**:
```php
// VULNERABLE - eval with user input
eval($_GET['code']); // Never use eval

// VULNERABLE - assert with user input
assert($_POST['condition']);

// VULNERABLE - create_function (deprecated)
$func = create_function('$a', $_GET['code']);

// VULNERABLE - preg_replace with /e modifier
preg_replace('/pattern/e', $_GET['replacement'], $string);

// VULNERABLE - Variable functions
$func = $_GET['function'];
$func(); // Can call any function
```

**Secure Alternative**:
```php
// Never use eval, assert, or create_function with user input
// Use whitelisting for allowed operations
$allowed_operations = ['add', 'subtract', 'multiply'];
$operation = $_GET['op'];

if (in_array($operation, $allowed_operations, true)) {
    switch ($operation) {
        case 'add':
            $result = $a + $b;
            break;
        // ... other cases
    }
}

// Use anonymous functions instead of create_function
$func = function($a) use ($b) {
    return $a + $b;
};
```

### 2. SQL Injection
**Risk**: Database compromise, data theft
**Detection Patterns**:
```php
// VULNERABLE - Direct concatenation
$query = "SELECT * FROM users WHERE id = " . $_GET['id'];
mysqli_query($conn, $query);

// VULNERABLE - mysql_* functions (deprecated)
$query = "SELECT * FROM users WHERE name = '" . $_POST['name'] . "'";
mysql_query($query);

// VULNERABLE - String interpolation
$query = "SELECT * FROM users WHERE email = '{$_POST['email']}'";

// VULNERABLE - PDO without prepared statements
$pdo->query("SELECT * FROM users WHERE id = " . $_GET['id']);
```

**Secure Alternative**:
```php
// Use prepared statements with PDO
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([$_GET['id']]);

// Or with named parameters
$stmt = $pdo->prepare("SELECT * FROM users WHERE email = :email");
$stmt->execute(['email' => $_POST['email']]);

// MySQLi prepared statements
$stmt = $mysqli->prepare("SELECT * FROM users WHERE id = ?");
$stmt->bind_param("i", $_GET['id']);
$stmt->execute();

// Use ORM (Laravel Eloquent, Doctrine)
$user = User::where('email', $email)->first();
```

### 3. Local/Remote File Inclusion (LFI/RFI)
**Risk**: Code execution, information disclosure
**Detection Patterns**:
```php
// VULNERABLE - include with user input
include($_GET['page'] . '.php');

// VULNERABLE - require
require($_POST['file']);

// VULNERABLE - include_once
include_once('../' . $_GET['module'] . '/index.php');

// VULNERABLE - file_get_contents with user URL
$content = file_get_contents($_GET['url']);
```

**Secure Alternative**:
```php
// Whitelist allowed files
$allowed_pages = ['home', 'about', 'contact'];
$page = $_GET['page'] ?? 'home';

if (in_array($page, $allowed_pages, true)) {
    include __DIR__ . "/pages/{$page}.php";
} else {
    include __DIR__ . "/pages/404.php";
}

// Use basename to prevent directory traversal
$file = basename($_GET['file']);
$filepath = __DIR__ . "/uploads/{$file}";

// Verify file exists and is within allowed directory
$realpath = realpath($filepath);
if ($realpath && strpos($realpath, __DIR__ . '/uploads/') === 0) {
    include $realpath;
}

// Disable allow_url_include in php.ini
// allow_url_include = Off
```

### 4. Unsafe Deserialization
**Risk**: Remote code execution
**Detection Patterns**:
```php
// VULNERABLE - unserialize with user input
$data = unserialize($_COOKIE['user_data']);

// VULNERABLE - unserialize from database without validation
$object = unserialize($row['serialized_data']);

// VULNERABLE - Phar deserialization
$phar = new Phar($_GET['file']);
```

**Secure Alternative**:
```php
// Use JSON instead of serialize
$data = json_decode($_COOKIE['user_data'], true);

// If serialization is necessary, sign the data
function safe_serialize($data, $key) {
    $serialized = serialize($data);
    $hmac = hash_hmac('sha256', $serialized, $key);
    return base64_encode($hmac . $serialized);
}

function safe_unserialize($data, $key) {
    $data = base64_decode($data);
    $hmac = substr($data, 0, 64);
    $serialized = substr($data, 64);
    
    if (hash_hmac('sha256', $serialized, $key) !== $hmac) {
        throw new Exception('Invalid signature');
    }
    
    return unserialize($serialized);
}

// Or use allowed_classes option (PHP 7.0+)
$data = unserialize($input, ['allowed_classes' => ['User', 'Product']]);
```

### 5. Type Juggling
**Risk**: Authentication bypass, logic flaws
**Detection Patterns**:
```php
// VULNERABLE - Loose comparison
if ($_POST['password'] == $stored_hash) { // '0e123' == '0e456' is true!
    login_user();
}

// VULNERABLE - in_array without strict mode
if (in_array($_GET['role'], ['admin', 'user'])) { // 0 == 'admin' is true!
    grant_access();
}

// VULNERABLE - strcmp with arrays
if (strcmp($_POST['password'], $correct_password) == 0) {
    // strcmp returns NULL for arrays, NULL == 0 is true!
}
```

**Secure Alternative**:
```php
// Use strict comparison (===)
if ($_POST['password'] === $stored_hash) {
    login_user();
}

// Use password_verify for password checking
if (password_verify($_POST['password'], $stored_hash)) {
    login_user();
}

// Use strict mode in in_array
if (in_array($_GET['role'], ['admin', 'user'], true)) {
    grant_access();
}

// Validate input types
if (is_string($_POST['password']) && strcmp($_POST['password'], $correct_password) === 0) {
    login_user();
}
```

### 6. Command Injection
**Risk**: Arbitrary command execution
**Detection Patterns**:
```php
// VULNERABLE - exec with user input
exec("ping -c 4 " . $_GET['host']);

// VULNERABLE - system
system("ls " . $_GET['directory']);

// VULNERABLE - shell_exec
$output = shell_exec("cat " . $_GET['file']);

// VULNERABLE - backticks
$output = `ping {$_GET['host']}`;

// VULNERABLE - passthru
passthru("convert " . $_GET['file'] . " output.png");
```

**Secure Alternative**:
```php
// Use escapeshellarg for arguments
$host = escapeshellarg($_GET['host']);
exec("ping -c 4 {$host}", $output);

// Better: Use escapeshellcmd for the entire command
$command = escapeshellcmd("ping -c 4 " . $_GET['host']);
exec($command, $output);

// Best: Avoid shell commands, use PHP functions
// Instead of: exec("ls " . $dir)
$files = scandir($dir);

// Instead of: exec("cat " . $file)
$content = file_get_contents($file);

// If shell is necessary, validate input
if (preg_match('/^[a-zA-Z0-9.-]+$/', $_GET['host'])) {
    exec("ping -c 4 " . $_GET['host'], $output);
}
```

### 7. Cross-Site Scripting (XSS)
**Risk**: Session hijacking, defacement
**Detection Patterns**:
```php
// VULNERABLE - Direct output
echo $_GET['name'];

// VULNERABLE - In HTML attributes
<input value="<?php echo $_POST['value']; ?>">

// VULNERABLE - In JavaScript
<script>var name = '<?php echo $_GET['name']; ?>';</script>

// VULNERABLE - In URLs
<a href="<?php echo $_GET['url']; ?>">Click</a>
```

**Secure Alternative**:
```php
// Use htmlspecialchars for HTML context
echo htmlspecialchars($_GET['name'], ENT_QUOTES, 'UTF-8');

// For HTML attributes
<input value="<?php echo htmlspecialchars($_POST['value'], ENT_QUOTES, 'UTF-8'); ?>">

// For JavaScript context, use json_encode
<script>var name = <?php echo json_encode($_GET['name']); ?>;</script>

// For URLs, use urlencode
<a href="<?php echo htmlspecialchars(urlencode($_GET['url']), ENT_QUOTES, 'UTF-8'); ?>">

// Laravel Blade (auto-escapes)
{{ $name }} // Escaped
{!! $html !!} // Unescaped (use carefully)
```

### 8. Path Traversal
**Risk**: Unauthorized file access
**Detection Patterns**:
```php
// VULNERABLE - Direct file access
$file = $_GET['file'];
readfile("/var/www/uploads/" . $file);

// VULNERABLE - No path validation
$filename = $_POST['filename'];
unlink("./temp/" . $filename);

// VULNERABLE - Insufficient validation
if (strpos($_GET['file'], '..') === false) {
    include $_GET['file']; // Still vulnerable to absolute paths
}
```

**Secure Alternative**:
```php
// Use basename to remove path components
$filename = basename($_GET['file']);
$filepath = "/var/www/uploads/" . $filename;

// Verify the resolved path is within allowed directory
$base_dir = realpath('/var/www/uploads');
$filepath = realpath('/var/www/uploads/' . $_GET['file']);

if ($filepath && strpos($filepath, $base_dir) === 0) {
    readfile($filepath);
} else {
    die('Access denied');
}

// Whitelist allowed files
$allowed_files = ['report.pdf', 'invoice.pdf'];
if (in_array($_GET['file'], $allowed_files, true)) {
    readfile('/var/www/uploads/' . $_GET['file']);
}
```

### 9. XML External Entity (XXE)
**Risk**: File disclosure, SSRF, DoS
**Detection Patterns**:
```php
// VULNERABLE - Default XML parsing
$xml = simplexml_load_string($_POST['xml']);

// VULNERABLE - DOMDocument without disabling entities
$dom = new DOMDocument();
$dom->loadXML($_POST['xml']);

// VULNERABLE - XMLReader
$reader = new XMLReader();
$reader->XML($_POST['xml']);
```

**Secure Alternative**:
```php
// Disable external entity loading
libxml_disable_entity_loader(true);

// For simplexml
$xml = simplexml_load_string($_POST['xml'], 'SimpleXMLElement', LIBXML_NOENT);

// For DOMDocument
$dom = new DOMDocument();
$dom->loadXML($_POST['xml'], LIBXML_NOENT | LIBXML_DTDLOAD | LIBXML_DTDATTR);

// Better: Use JSON instead of XML when possible
$data = json_decode($_POST['data'], true);
```

### 10. Session Fixation
**Risk**: Session hijacking
**Detection Patterns**:
```php
// VULNERABLE - No session regeneration after login
session_start();
if (verify_credentials($_POST['username'], $_POST['password'])) {
    $_SESSION['user_id'] = $user_id;
    // No session_regenerate_id()
}

// VULNERABLE - Accepting session ID from GET/POST
session_id($_GET['PHPSESSID']);
session_start();
```

**Secure Alternative**:
```php
// Regenerate session ID after login
session_start();
if (verify_credentials($_POST['username'], $_POST['password'])) {
    session_regenerate_id(true); // Delete old session
    $_SESSION['user_id'] = $user_id;
}

// Secure session configuration
ini_set('session.cookie_httponly', 1);
ini_set('session.cookie_secure', 1); // HTTPS only
ini_set('session.cookie_samesite', 'Strict');
ini_set('session.use_strict_mode', 1);
ini_set('session.use_only_cookies', 1);

// Or in php.ini
// session.cookie_httponly = 1
// session.cookie_secure = 1
// session.cookie_samesite = Strict
```

## Framework-Specific Security

### Laravel Security
```php
// Use Query Builder (auto-escapes)
$users = DB::table('users')->where('email', $email)->get();

// Use Eloquent ORM
$user = User::where('email', $email)->first();

// CSRF protection (enabled by default)
<form method="POST">
    @csrf
    <!-- form fields -->
</form>

// Mass assignment protection
class User extends Model {
    protected $fillable = ['name', 'email'];
    // or
    protected $guarded = ['is_admin'];
}

// XSS protection (Blade auto-escapes)
{{ $user->name }} // Escaped
{!! $html !!} // Unescaped (use carefully)
```

### WordPress Security
```php
// Use wpdb for database queries
global $wpdb;
$user = $wpdb->get_row($wpdb->prepare(
    "SELECT * FROM {$wpdb->users} WHERE ID = %d",
    $user_id
));

// Sanitize input
$clean_email = sanitize_email($_POST['email']);
$clean_text = sanitize_text_field($_POST['name']);
$clean_html = wp_kses_post($_POST['content']);

// Escape output
echo esc_html($user_input);
echo esc_attr($attribute_value);
echo esc_url($url);

// Nonce verification
if (wp_verify_nonce($_POST['_wpnonce'], 'my_action')) {
    // Process form
}
```

## Common Vulnerable Packages
**Check for CVEs**:
- `symfony/symfony` < 6.3.8
- `laravel/framework` < 10.32.1
- `guzzlehttp/guzzle` < 7.8.0
- `monolog/monolog` < 3.5.0
- `phpmailer/phpmailer` < 6.9.1
- `twig/twig` < 3.8.0

## Security Checklist

### Input Validation
- [ ] All user input validated and sanitized
- [ ] SQL injection prevention (prepared statements)
- [ ] Command injection prevention
- [ ] Path traversal prevention
- [ ] XSS prevention (htmlspecialchars)

### Authentication
- [ ] Passwords hashed with password_hash()
- [ ] Session regeneration after login
- [ ] Secure session configuration
- [ ] CSRF protection enabled
- [ ] Rate limiting on login

### Configuration
- [ ] display_errors = Off in production
- [ ] expose_php = Off
- [ ] allow_url_include = Off
- [ ] open_basedir restrictions
- [ ] disable_functions for dangerous functions

### File Operations
- [ ] File upload validation (type, size)
- [ ] Path traversal prevention
- [ ] Proper file permissions
- [ ] No execution of uploaded files

- [ ] No execution of uploaded files

## Advanced PHP Security Discovery (Discovery Focus)

### 1. Deserialization with PHPGGC
**Methodology**: Detect object injection beyond simple `unserialize` grep.
*   **Technique**: Use `PHPGGC` to generate gadget chains for installed libraries (Laravel/Symfony).
*   **Action**:
    1.  Identify any user input passed to `unserialize()`.
    2.  Check if `phar://` wrapper can be triggered via `file_exists()` or `fopen()`.
    3.  Generate payloads: `./phpggc Laravel/RCE1 system "id"` and inject.

### 2. Type Juggling Fuzzing
**Methodology**: Detect loose comparison bypasses.
*   **Audit**: Grep for `==` and `!=` involving hashes or tokens.
*   **Payloads**:
    *   Magic Hashes: `0e123...` (MD5 collision)
    *   Array bypass: `param[]=1` (e.g. `strcmp([], "string")` returns `NULL` which is falsy/0 in older PHP).
    *   JSON bypass: `{"param": true}` (vs string "true").

### 3. Wrapper Injection Discovery
**Methodology**: Identify LFI via PHP protocols.
*   **Audit**: Grep for `include`, `require`, `fopen`, `file_get_contents`.
*   **Payloads**:
    *   `php://filter/convert.base64-encode/resource=index.php` (Read source code)
    *   `data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7Pz4=` (RCE)
    *   `expect://id` (Command execution, requires plugin)

### 4. Zero Tolerance Data Compromise Protocol
**Mandate**: Prevent debug leakage.
*   **Check**:
    1.  Ensure `phpinfo()` is NEVER reachable.
    2.  Check if `.env` or `config.php` are accessible via web (try direct URL).
    3.  Verify `display_errors` is OFF. Matches of "Fatal error:" in HTTP responses = **CRITICAL**.
```
"[package-name]" composer CVE vulnerability
"[package-name]" packagist security advisory
"php" "[vulnerability-type]" exploit
"Laravel" security best practices 2024
composer audit [package-name]
```

## References
- [OWASP PHP Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/PHP_Configuration_Cheat_Sheet.html)
- [PHP Security Guide](https://www.php.net/manual/en/security.php)
- [Packagist Security Advisories](https://packagist.org/)
