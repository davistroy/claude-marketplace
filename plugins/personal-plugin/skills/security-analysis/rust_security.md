# Rust Security Analysis

## Dependency Scanning Commands

```bash
# Check for known vulnerabilities
cargo install cargo-audit
cargo audit

# Check for outdated dependencies
cargo install cargo-outdated
cargo outdated

# Update dependencies
cargo update
```

## Critical Vulnerability Patterns

### 1. Unsafe Code Blocks
```rust
// VULNERABLE - Unsafe without justification
unsafe {
    let ptr = user_input as *const i32;
    *ptr // Potential segfault
}

// SECURE - Minimize unsafe, document why needed
// SAFETY: ptr is guaranteed to be valid because...
unsafe {
    *ptr
}
```

### 2. SQL Injection
```rust
// VULNERABLE
let query = format!("SELECT * FROM users WHERE id = {}", user_id);
conn.execute(&query, [])?;

// SECURE - Use parameterized queries
use rusqlite::params;
conn.query_row(
    "SELECT * FROM users WHERE id = ?1",
    params![user_id],
    |row| Ok(row.get(0)?)
)?;

// Or use an ORM like Diesel
users.filter(id.eq(user_id)).first(&conn)?
```

### 3. Command Injection
```rust
// VULNERABLE
use std::process::Command;
Command::new("sh")
    .arg("-c")
    .arg(format!("ping {}", user_input))
    .output()?;

// SECURE
Command::new("ping")
    .arg("-c")
    .arg("4")
    .arg(&user_input) // Passed as separate argument
    .output()?;

// Validate input
if !user_input.chars().all(|c| c.is_alphanumeric() || c == '.' || c == '-') {
    return Err("Invalid input");
}
```

### 4. Path Traversal
```rust
// VULNERABLE
use std::fs;
let path = format!("/uploads/{}", user_input);
fs::read_to_string(path)?;

// SECURE
use std::path::{Path, PathBuf};

fn safe_path(base: &Path, user_input: &str) -> Result<PathBuf, Error> {
    let path = base.join(user_input);
    let canonical = path.canonicalize()?;
    
    if !canonical.starts_with(base) {
        return Err("Path traversal detected");
    }
    
    Ok(canonical)
}
```

### 5. Integer Overflow
```rust
// VULNERABLE - Can panic in debug, wrap in release
let result = a + b;

// SECURE - Checked arithmetic
let result = a.checked_add(b).ok_or("Overflow")?;

// Or use saturating arithmetic
let result = a.saturating_add(b);

// Or wrapping (if intended)
let result = a.wrapping_add(b);
```

### 6. Weak Random Generation
```rust
// VULNERABLE - Predictable
use rand::Rng;
let mut rng = rand::thread_rng();
let token = rng.gen::<u64>();

// SECURE - Cryptographically secure
use rand::rngs::OsRng;
use rand::RngCore;

let mut token = [0u8; 32];
OsRng.fill_bytes(&mut token);
```

## Web Framework Security (Actix/Axum)

### Input Validation
```rust
use serde::Deserialize;
use validator::Validate;

#[derive(Deserialize, Validate)]
struct UserInput {
    #[validate(length(min = 3, max = 20))]
    #[validate(regex = "^[a-zA-Z0-9_-]+$")]
    username: String,
    
    #[validate(email)]
    email: String,
}

async fn create_user(input: Json<UserInput>) -> Result<Json<User>> {
    input.validate()?;
    // Process...
}
```

### Authentication
```rust
use jsonwebtoken::{encode, decode, Header, Validation, EncodingKey, DecodingKey};

let token = encode(
    &Header::default(),
    &claims,
    &EncodingKey::from_secret(secret.as_ref())
)?;

let token_data = decode::<Claims>(
    &token,
    &DecodingKey::from_secret(secret.as_ref()),
    &Validation::default()
)?;
```

## Common Vulnerable Packages
- `actix-web` < 4.4.0
- `tokio` < 1.35.0
- `hyper` < 0.14.27
- `rustls` < 0.21.9

## Advanced Rust Security Discovery (Discovery Focus)

### 1. Targeted Unsafe Fuzzing
**Methodology**: Focus dynamic testing specifically on `unsafe` blocks.
*   **Technique**: Use `cargo-fuzz` (libFuzzer) or `FourFuzz` logic.
*   **Action**:
    1.  Create a fuzz target that wraps the API exposing unsafe behavior.
    2.  `cargo fuzz run my_target`
    3.  **Audit**: Manually review all `unsafe` blocks. If `// SAFETY:` comments are missing or weak, flag as **HIGH**.

### 2. FFI Boundary Auditing
**Methodology**: Verify memory safety at the "Safe-to-Unsafe" boundary.
*   **Action**:
    1.  Check `extern "C"` functions.
    2.  Verify input pointers are not null using `ptr::as_ref()`.
    3.  Verify strings are valid UTF-8 if converting to `String`.
    4.  Verify slice lengths from raw parts are correct.

### 3. Dependency Unsafe Count
**Methodology**: Quantify risk from dependencies.
*   **Tool**: `cargo-geiger`
*   **Action**:
    1.  Run `cargo geiger`.
    2.  If a dependency has a high count of `unsafe` blocks and is not standard (like `tokio`), flagged for deep review.

### 4. Zero Tolerance Data Compromise Protocol
**Mandate**: Ensure memory corruption does not leak data.
*   **Check**:
    1.  Run under `miri` (Undefined Behavior detector) checks if possible.
    2.  Run address sanitizer (`-Z sanitizer=address`).
    3.  If any memory leak or use-after-free is detected, flag as **CRITICAL**.

## References
- [RustSec Advisory Database](https://rustsec.org/)
- [Rust Security Guidelines](https://anssi-fr.github.io/rust-guide/)
