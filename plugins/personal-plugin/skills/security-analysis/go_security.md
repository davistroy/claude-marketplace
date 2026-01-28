# Go Security Analysis

## Overview
Go applications benefit from memory safety but still face security challenges from SQL injection, command injection, race conditions, and dependency vulnerabilities.

## Dependency Scanning Commands

### Go Vulnerability Check
```bash
# Check for known vulnerabilities (Go 1.18+)
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...

# Check for outdated modules
go list -m -u all

# Update dependencies
go get -u ./...
go mod tidy

# Vendor dependencies for reproducible builds
go mod vendor
```

## Critical Vulnerability Patterns

### 1. SQL Injection
**Risk**: Database compromise
**Detection Patterns**:
```go
// VULNERABLE - String concatenation
query := "SELECT * FROM users WHERE id = " + userID
db.Query(query)

// VULNERABLE - fmt.Sprintf
query := fmt.Sprintf("SELECT * FROM users WHERE email = '%s'", email)
rows, err := db.Query(query)

// VULNERABLE - String interpolation
db.Exec(`DELETE FROM users WHERE id = ` + id)
```

**Secure Alternative**:
```go
// Use parameterized queries
query := "SELECT * FROM users WHERE id = $1"
rows, err := db.Query(query, userID)

// Multiple parameters
query := "SELECT * FROM users WHERE email = $1 AND active = $2"
rows, err := db.Query(query, email, true)

// Use ORM (GORM)
var user User
db.Where("email = ?", email).First(&user)

// sqlx with named parameters
query := "SELECT * FROM users WHERE email = :email"
rows, err := db.NamedQuery(query, map[string]interface{}{"email": email})
```

### 2. Command Injection
**Risk**: Arbitrary command execution
**Detection Patterns**:
```go
// VULNERABLE - exec.Command with shell
cmd := exec.Command("sh", "-c", "ping "+userInput)
cmd.Run()

// VULNERABLE - String concatenation in command
cmd := exec.Command("ping", "-c", "4", userInput) // Still vulnerable if userInput contains shell metacharacters
```

**Secure Alternative**:
```go
// Validate input first
import "regexp"

func isValidHostname(host string) bool {
    match, _ := regexp.MatchString(`^[a-zA-Z0-9.-]+$`, host)
    return match
}

if !isValidHostname(userInput) {
    return errors.New("invalid hostname")
}

// Use exec.Command without shell
cmd := exec.Command("ping", "-c", "4", userInput)
output, err := cmd.CombinedOutput()

// Better: Use Go libraries instead of shell commands
// Instead of: exec.Command("ls", directory)
files, err := os.ReadDir(directory)
```

### 3. Path Traversal
**Risk**: Unauthorized file access
**Detection Patterns**:
```go
// VULNERABLE - Direct file access
filename := r.URL.Query().Get("file")
data, err := os.ReadFile("/uploads/" + filename)

// VULNERABLE - filepath.Join without validation
filepath := filepath.Join("/uploads", userInput)
os.Remove(filepath)
```

**Secure Alternative**:
```go
import (
    "path/filepath"
    "strings"
)

// Clean and validate path
func safeFilePath(baseDir, userPath string) (string, error) {
    // Clean the path
    cleanPath := filepath.Clean(userPath)
    
    // Join with base directory
    fullPath := filepath.Join(baseDir, cleanPath)
    
    // Resolve to absolute path
    absPath, err := filepath.Abs(fullPath)
    if err != nil {
        return "", err
    }
    
    // Ensure it's within base directory
    absBase, err := filepath.Abs(baseDir)
    if err != nil {
        return "", err
    }
    
    if !strings.HasPrefix(absPath, absBase) {
        return "", errors.New("path traversal detected")
    }
    
    return absPath, nil
}

// Usage
safePath, err := safeFilePath("/uploads", userInput)
if err != nil {
    return err
}
data, err := os.ReadFile(safePath)
```

### 4. Race Conditions
**Risk**: Data corruption, security bypass
**Detection Patterns**:
```go
// VULNERABLE - TOCTOU (Time-of-check to time-of-use)
if _, err := os.Stat(filename); err == nil {
    // File exists
    os.Remove(filename) // Another goroutine might have deleted it
}

// VULNERABLE - Unsynchronized map access
var cache = make(map[string]string)

func get(key string) string {
    return cache[key] // Race condition if accessed from multiple goroutines
}

func set(key, value string) {
    cache[key] = value // Race condition
}
```

**Secure Alternative**:
```go
// Use sync.Mutex for synchronization
import "sync"

type SafeCache struct {
    mu    sync.RWMutex
    cache map[string]string
}

func (c *SafeCache) Get(key string) string {
    c.mu.RLock()
    defer c.mu.RUnlock()
    return c.cache[key]
}

func (c *SafeCache) Set(key, value string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.cache[key] = value
}

// Or use sync.Map for concurrent access
var cache sync.Map

func get(key string) (string, bool) {
    value, ok := cache.Load(key)
    if !ok {
        return "", false
    }
    return value.(string), true
}

func set(key, value string) {
    cache.Store(key, value)
}

// Use atomic operations for simple values
import "sync/atomic"

var counter int64

func increment() {
    atomic.AddInt64(&counter, 1)
}
```

### 5. Weak Cryptography
**Risk**: Data exposure
**Detection Patterns**:
```go
// VULNERABLE - MD5/SHA1 for passwords
import "crypto/md5"
hash := md5.Sum([]byte(password))

// VULNERABLE - Weak random
import "math/rand"
token := rand.Intn(1000000) // Predictable

// VULNERABLE - ECB mode
import "crypto/aes"
cipher, _ := aes.NewCipher(key)
cipher.Encrypt(dst, src) // Direct encryption without mode
```

**Secure Alternative**:
```go
// Use bcrypt for passwords
import "golang.org/x/crypto/bcrypt"

func hashPassword(password string) (string, error) {
    hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
    return string(hash), err
}

func checkPassword(password, hash string) bool {
    err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
    return err == nil
}

// Use crypto/rand for random values
import "crypto/rand"
import "encoding/base64"

func generateToken(length int) (string, error) {
    bytes := make([]byte, length)
    if _, err := rand.Read(bytes); err != nil {
        return "", err
    }
    return base64.URLEncoding.EncodeToString(bytes), nil
}

// Use GCM mode for encryption
import (
    "crypto/aes"
    "crypto/cipher"
    "crypto/rand"
)

func encrypt(plaintext, key []byte) ([]byte, error) {
    block, err := aes.NewCipher(key)
    if err != nil {
        return nil, err
    }
    
    gcm, err := cipher.NewGCM(block)
    if err != nil {
        return nil, err
    }
    
    nonce := make([]byte, gcm.NonceSize())
    if _, err := rand.Read(nonce); err != nil {
        return nil, err
    }
    
    return gcm.Seal(nonce, nonce, plaintext, nil), nil
}
```

### 6. Unsafe Reflection
**Risk**: Type confusion, security bypass
**Detection Patterns**:
```go
// VULNERABLE - Reflection with user input
import "reflect"

funcName := r.URL.Query().Get("func")
method := reflect.ValueOf(obj).MethodByName(funcName)
method.Call([]reflect.Value{})

// VULNERABLE - Type assertion without checking
value := userInput.(string) // Panics if wrong type
```

**Secure Alternative**:
```go
// Whitelist allowed methods
allowedMethods := map[string]bool{
    "GetUser": true,
    "ListItems": true,
}

funcName := r.URL.Query().Get("func")
if !allowedMethods[funcName] {
    return errors.New("method not allowed")
}

method := reflect.ValueOf(obj).MethodByName(funcName)
if !method.IsValid() {
    return errors.New("method not found")
}

// Safe type assertion
value, ok := userInput.(string)
if !ok {
    return errors.New("invalid type")
}
```

### 7. Improper Error Handling
**Risk**: Information disclosure
**Detection Patterns**:
```go
// VULNERABLE - Exposing internal errors
func handler(w http.ResponseWriter, r *http.Request) {
    user, err := getUser(id)
    if err != nil {
        http.Error(w, err.Error(), 500) // Exposes internal details
    }
}

// VULNERABLE - Logging sensitive data
log.Printf("User login: %s with password: %s", username, password)
```

**Secure Alternative**:
```go
// Generic error messages to users
func handler(w http.ResponseWriter, r *http.Request) {
    user, err := getUser(id)
    if err != nil {
        // Log detailed error server-side
        log.Printf("Error getting user %s: %v", id, err)
        
        // Return generic message to client
        http.Error(w, "Internal server error", 500)
        return
    }
}

// Don't log sensitive data
log.Printf("User login attempt: %s", username)
// Never log passwords, tokens, or PII
```

### 8. SSRF (Server-Side Request Forgery)
**Risk**: Internal network access
**Detection Patterns**:
```go
// VULNERABLE - Fetching user-provided URLs
url := r.URL.Query().Get("url")
resp, err := http.Get(url) // Can access internal services

// VULNERABLE - No URL validation
client := &http.Client{}
req, _ := http.NewRequest("GET", userURL, nil)
resp, _ := client.Do(req)
```

**Secure Alternative**:
```go
import (
    "net"
    "net/url"
)

func isAllowedURL(rawURL string) error {
    parsedURL, err := url.Parse(rawURL)
    if err != nil {
        return err
    }
    
    // Only allow HTTP/HTTPS
    if parsedURL.Scheme != "http" && parsedURL.Scheme != "https" {
        return errors.New("invalid scheme")
    }
    
    // Resolve hostname
    ips, err := net.LookupIP(parsedURL.Hostname())
    if err != nil {
        return err
    }
    
    // Block private IP ranges
    for _, ip := range ips {
        if isPrivateIP(ip) {
            return errors.New("private IP not allowed")
        }
    }
    
    return nil
}

func isPrivateIP(ip net.IP) bool {
    privateRanges := []string{
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "127.0.0.0/8",
    }
    
    for _, cidr := range privateRanges {
        _, subnet, _ := net.ParseCIDR(cidr)
        if subnet.Contains(ip) {
            return true
        }
    }
    return false
}

// Usage
if err := isAllowedURL(userURL); err != nil {
    return err
}
resp, err := http.Get(userURL)
```

## Framework-Specific Security

### Gin Framework
```go
import "github.com/gin-gonic/gin"

// Input validation
type LoginInput struct {
    Username string `json:"username" binding:"required,alphanum,min=3,max=20"`
    Password string `json:"password" binding:"required,min=8"`
}

func login(c *gin.Context) {
    var input LoginInput
    if err := c.ShouldBindJSON(&input); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }
    // Process login
}

// CORS configuration
import "github.com/gin-contrib/cors"

config := cors.Config{
    AllowOrigins:     []string{"https://yourdomain.com"},
    AllowMethods:     []string{"GET", "POST", "PUT", "DELETE"},
    AllowHeaders:     []string{"Authorization", "Content-Type"},
    AllowCredentials: true,
}
router.Use(cors.New(config))

// Rate limiting
import "github.com/gin-contrib/limiter"

store := limiter.NewMemoryStore()
rate := limiter.Rate{
    Period: 1 * time.Minute,
    Limit:  100,
}
router.Use(limiter.NewMiddleware(store, rate))
```

## Common Vulnerable Packages
**Check for CVEs**:
- `github.com/gin-gonic/gin` < 1.9.1
- `github.com/gorilla/websocket` < 1.5.0
- `golang.org/x/crypto` < 0.17.0
- `golang.org/x/net` < 0.17.0
- `github.com/dgrijalva/jwt-go` (deprecated, use golang-jwt/jwt)

## Security Checklist
- [ ] SQL injection prevention (parameterized queries)
- [ ] Command injection prevention
- [ ] Path traversal prevention
- [ ] Race condition prevention (mutexes)
- [ ] Secure random generation (crypto/rand)
- [ ] Proper error handling
- [ ] SSRF prevention
- [ ] Input validation
- [ ] Dependencies updated (govulncheck)

## Advanced Go Security Discovery (Discovery Focus)

### 1. Fuzzing with Go Native Fuzzing (1.18+)
**Methodology**: Use Go's built-in fuzzer to crash parsers and logic.
*   **Technique**: Write `FuzzXxx(f *testing.F)` functions.
*   **Action**:
    ```go
    func FuzzParseQuery(f *testing.F) {
        f.Add("key=value")
        f.Fuzz(func(t *testing.T, input string) {
            ParseQuery(input) // Look for panics/crashes
        })
    }
    ```
*   **Run**: `go test -fuzz=FuzzParseQuery`

### 2. Race Detector in CI
**Methodology**: Catch concurrency bugs that lead to data corruption.
*   **Action**:
    1.  Add `-race` flag to all test runs: `go test -race ./...`.
    2.  Use `uber-go/goleak` to detect goroutine leaks in tests.

### 3. SSRF & Unsafe Pointer Discovery
**Methodology**: Find where network calls accept user input.
*   **Audit**: Grep for `http.Get(`, `http.NewRequest(`, `net.Dial(`.
*   **Trace**: Backtrack arguments to `func` params.
*   **Unsafe**: Grep for `unsafe.Pointer` usage which bypasses Go type safety.

### 4. Zero Tolerance Data Compromise Protocol
**Mandate**: Prevent leakage of goroutine stacks and pprof data.
*   **Check**:
    1.  Ensure `pprof` routes (`/debug/pprof`) are NOT exposed on public ports.
    2.  Check if `panic` output includes environment variables.
    3.  Flag any usage of `fmt.Println(secret)` -> must use `fmt.Println("REDACTED")`.

## Web Search Queries
```
"[package-name]" go CVE vulnerability
"[package-name]" golang security advisory
govulncheck [package-name]
"go security best practices" 2024
```

## References
- [Go Security](https://go.dev/security/)
- [OWASP Go Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Go_SCP_Cheat_Sheet.html)
