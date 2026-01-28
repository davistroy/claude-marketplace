# .NET / C# Security Analysis

## Dependency Scanning Commands

```bash
# Check for vulnerable packages
dotnet list package --vulnerable

# Check for outdated packages
dotnet list package --outdated

# Update packages
dotnet add package [PackageName]

# OWASP Dependency-Check
dependency-check --project myapp --scan bin/
```

## Critical Vulnerability Patterns

### 1. Unsafe Deserialization
```csharp
// VULNERABLE
BinaryFormatter formatter = new BinaryFormatter();
object obj = formatter.Deserialize(stream); // RCE risk

// SECURE
using System.Text.Json;
var obj = JsonSerializer.Deserialize<MyClass>(jsonString);
```

### 2. SQL Injection
```csharp
// VULNERABLE
string query = $"SELECT * FROM Users WHERE Id = {userId}";
SqlCommand cmd = new SqlCommand(query, connection);

// SECURE
string query = "SELECT * FROM Users WHERE Id = @userId";
SqlCommand cmd = new SqlCommand(query, connection);
cmd.Parameters.AddWithValue("@userId", userId);

// Or use Entity Framework
var user = context.Users.FirstOrDefault(u => u.Id == userId);
```

### 3. XSS in Razor Views
```csharp
// VULNERABLE
@Html.Raw(userInput)

// SECURE
@userInput  // Auto-escaped
@Html.Encode(userInput)
```

### 4. Path Traversal
```csharp
// VULNERABLE
string path = Path.Combine(baseDir, userInput);
File.ReadAllText(path);

// SECURE
string fullPath = Path.GetFullPath(Path.Combine(baseDir, userInput));
if (!fullPath.StartsWith(baseDir))
    throw new SecurityException("Path traversal detected");
```

### 5. Weak Cryptography
```csharp
// VULNERABLE
using var md5 = MD5.Create();
byte[] hash = md5.ComputeHash(Encoding.UTF8.GetBytes(password));

// SECURE - Use BCrypt or Argon2
using BCrypt.Net;
string hashedPassword = BCrypt.HashPassword(password);
bool isValid = BCrypt.Verify(password, hashedPassword);

// Secure random
using var rng = RandomNumberGenerator.Create();
byte[] token = new byte[32];
rng.GetBytes(token);
```

## ASP.NET Core Security

### Authentication & Authorization
```csharp
services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options => {
        options.TokenValidationParameters = new TokenValidationParameters {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = Configuration["Jwt:Issuer"],
            ValidAudience = Configuration["Jwt:Audience"],
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(Configuration["Jwt:Key"]))
        };
    });

[Authorize(Roles = "Admin")]
public class AdminController : Controller { }
```

### CSRF Protection
```csharp
services.AddAntiforgery(options => {
    options.HeaderName = "X-CSRF-TOKEN";
});

[ValidateAntiForgeryToken]
public IActionResult Create(Model model) { }
```

### Input Validation
```csharp
public class UserModel {
    [Required]
    [StringLength(20, MinimumLength = 3)]
    [RegularExpression(@"^[a-zA-Z0-9_-]+$")]
    public string Username { get; set; }
    
    [Required]
    [EmailAddress]
    public string Email { get; set; }
}
```

## Common Vulnerable Packages
- `Newtonsoft.Json` < 13.0.3
- `System.Text.Json` < 7.0.3
- `Microsoft.AspNetCore.Mvc` < 2.2.0

## Advanced .NET Security Discovery (Discovery Focus)

### 1. Deserialization Gadget Detection
**Methodology**: Identify usage of dangerous serializers.
*   **Audit**: Grep for usage of types that allow "Type Handling".
    *   `TypeNameHandling.All` or `Auto` (Newtonsoft)
    *   `BinaryFormatter` (Obsolete but dangerous)
    *   `JavaScriptSerializer` (Legacy)
*   **Trace**: Check if `deserialize(string)` is called with user data.
*   **Action**: Trace if any class in the classpath has a dangerous destructor (Gadget).

### 2. LINQ Injection Discovery
**Methodology**: Dynamic LINQ libraries can allow expression injection.
*   **Audit**: Grep for `injections`.
*   **Pattern**: usage of `System.Linq.Dynamic`.
    ```csharp
    // VULNERABLE
    var result = db.Users.Where("Id == " + input);
    ```
*   **Zero Tolerance**: Any string concatenation inside `Where()` string overloads is **CRITICAL**.

### 3. Mass Assignment / Over-Posting
**Methodology**: Binding models to Entity Framework entities directly.
*   **Audit**: Check controller actions taking raw Entities.
    ```csharp
    public IActionResult Update([Bind("Id,Name")] User user) { ... }
    ```
*   **Check**: Are sensitive fields like `IsAdmin` or `Balance` implicitly bound?

### 4. Zero Tolerance Data Compromise Protocol
**Mandate**: Prevent leakage of PII in exceptions.
*   **Check**:
    1.  Ensure `ASPNETCORE_ENVIRONMENT` is NOT `Development` in prod.
    2.  Check for `UseDeveloperExceptionPage()` usage in `Startup.cs`.
    3.  Verify that `appsettings.json` does not contain unencrypted connection strings.

## References
- [OWASP .NET Security](https://owasp.org/www-project-dotnet-security/)
- [ASP.NET Core Security](https://docs.microsoft.com/en-us/aspnet/core/security/)
