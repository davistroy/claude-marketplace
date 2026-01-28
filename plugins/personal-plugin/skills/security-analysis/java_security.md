# Java / Kotlin Security Analysis

## Overview
Java applications face security challenges from deserialization, XXE, SQL injection, and framework-specific vulnerabilities.

## Dependency Scanning Commands

### Maven
```bash
# OWASP Dependency-Check
mvn org.owasp:dependency-check-maven:check

# Check for updates
mvn versions:display-dependency-updates

# Snyk scan
snyk test --all-projects
```

### Gradle
```bash
# OWASP Dependency-Check
./gradlew dependencyCheckAnalyze

# Check for updates
./gradlew dependencyUpdates

# Snyk scan
snyk test --all-projects
```

## Critical Vulnerability Patterns

### 1. Unsafe Deserialization
**Risk**: Remote code execution
**Detection Patterns**:
```java
// VULNERABLE - ObjectInputStream with untrusted data
ObjectInputStream ois = new ObjectInputStream(userInputStream);
Object obj = ois.readObject(); // Can execute arbitrary code

// VULNERABLE - XMLDecoder
XMLDecoder decoder = new XMLDecoder(userInputStream);
Object obj = decoder.readObject();

// VULNERABLE - XStream without security
XStream xstream = new XStream();
Object obj = xstream.fromXML(userInput);
```

**Secure Alternative**:
```java
// Use JSON instead of Java serialization
import com.fasterxml.jackson.databind.ObjectMapper;

ObjectMapper mapper = new ObjectMapper();
MyObject obj = mapper.readValue(jsonString, MyObject.class);

// If serialization is necessary, use allowlist
import org.apache.commons.lang3.SerializationUtils;

// Implement custom ObjectInputStream with class filtering
class SecureObjectInputStream extends ObjectInputStream {
    private static final Set<String> ALLOWED_CLASSES = Set.of(
        "com.example.SafeClass1",
        "com.example.SafeClass2"
    );
    
    @Override
    protected Class<?> resolveClass(ObjectStreamClass desc) 
            throws IOException, ClassNotFoundException {
        if (!ALLOWED_CLASSES.contains(desc.getName())) {
            throw new InvalidClassException("Unauthorized deserialization attempt");
        }
        return super.resolveClass(desc);
    }
}

// XStream with security
XStream xstream = new XStream();
xstream.addPermission(NoTypePermission.NONE);
xstream.addPermission(new ExplicitTypePermission(new Class[]{MyClass.class}));
```

### 2. SQL Injection
**Risk**: Database compromise
**Detection Patterns**:
```java
// VULNERABLE - String concatenation
String query = "SELECT * FROM users WHERE id = " + userId;
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery(query);

// VULNERABLE - String.format
String query = String.format("SELECT * FROM users WHERE email = '%s'", email);

// VULNERABLE - JPA native query without parameters
String query = "SELECT u FROM User u WHERE u.email = '" + email + "'";
Query q = em.createQuery(query);
```

**Secure Alternative**:
```java
// Use PreparedStatement
String query = "SELECT * FROM users WHERE id = ?";
PreparedStatement pstmt = conn.prepareStatement(query);
pstmt.setInt(1, userId);
ResultSet rs = pstmt.executeQuery();

// JPA with parameters
String query = "SELECT u FROM User u WHERE u.email = :email";
TypedQuery<User> q = em.createQuery(query, User.class);
q.setParameter("email", email);
List<User> users = q.getResultList();

// Spring Data JPA (preferred)
public interface UserRepository extends JpaRepository<User, Long> {
    User findByEmail(String email);
    
    @Query("SELECT u FROM User u WHERE u.email = :email")
    User findByEmailCustom(@Param("email") String email);
}
```

### 3. XML External Entity (XXE)
**Risk**: File disclosure, SSRF, DoS
**Detection Patterns**:
```java
// VULNERABLE - Default DocumentBuilder
DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
DocumentBuilder builder = factory.newDocumentBuilder();
Document doc = builder.parse(userInputStream);

// VULNERABLE - SAXParser
SAXParserFactory factory = SAXParserFactory.newInstance();
SAXParser parser = factory.newSAXParser();
parser.parse(userInputStream, handler);

// VULNERABLE - XMLReader
XMLReader reader = XMLReaderFactory.createXMLReader();
reader.parse(new InputSource(userInputStream));
```

**Secure Alternative**:
```java
// Secure DocumentBuilder
DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
factory.setXIncludeAware(false);
factory.setExpandEntityReferences(false);

DocumentBuilder builder = factory.newDocumentBuilder();
Document doc = builder.parse(userInputStream);

// Secure SAXParser
SAXParserFactory factory = SAXParserFactory.newInstance();
factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);

SAXParser parser = factory.newSAXParser();
parser.parse(userInputStream, handler);
```

### 4. Path Traversal
**Risk**: Unauthorized file access
**Detection Patterns**:
```java
// VULNERABLE - Direct file access
String filename = request.getParameter("file");
File file = new File("/uploads/" + filename);
FileInputStream fis = new FileInputStream(file);

// VULNERABLE - Insufficient validation
if (!filename.contains("..")) {
    File file = new File("/uploads/" + filename); // Still vulnerable
}
```

**Secure Alternative**:
```java
import java.nio.file.Path;
import java.nio.file.Paths;

public File getSecureFile(String userInput) throws IOException {
    // Normalize and resolve the path
    Path basePath = Paths.get("/uploads").toRealPath();
    Path requestedPath = basePath.resolve(userInput).normalize();
    
    // Ensure the resolved path is within the base directory
    if (!requestedPath.startsWith(basePath)) {
        throw new SecurityException("Path traversal attempt detected");
    }
    
    return requestedPath.toFile();
}

// Usage
try {
    File file = getSecureFile(request.getParameter("file"));
    FileInputStream fis = new FileInputStream(file);
} catch (SecurityException e) {
    // Handle security violation
}
```

### 5. Command Injection
**Risk**: Arbitrary command execution
**Detection Patterns**:
```java
// VULNERABLE - Runtime.exec with user input
String command = "ping " + userInput;
Runtime.getRuntime().exec(command);

// VULNERABLE - ProcessBuilder with shell
ProcessBuilder pb = new ProcessBuilder("sh", "-c", "ping " + userInput);
pb.start();
```

**Secure Alternative**:
```java
// Use ProcessBuilder with array (no shell)
String[] command = {"ping", "-c", "4", userInput};
ProcessBuilder pb = new ProcessBuilder(command);
Process process = pb.start();

// Validate input first
if (!userInput.matches("^[a-zA-Z0-9.-]+$")) {
    throw new IllegalArgumentException("Invalid input");
}

// Better: Use Java libraries instead of shell commands
// Instead of: Runtime.exec("ls " + directory)
File dir = new File(directory);
String[] files = dir.list();
```

### 6. Weak Cryptography
**Risk**: Data exposure
**Detection Patterns**:
```java
// VULNERABLE - MD5/SHA1 for passwords
MessageDigest md = MessageDigest.getInstance("MD5");
byte[] hash = md.digest(password.getBytes());

// VULNERABLE - Weak random
Random random = new Random();
int token = random.nextInt();

// VULNERABLE - DES encryption
Cipher cipher = Cipher.getInstance("DES");

// VULNERABLE - ECB mode
Cipher cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");
```

**Secure Alternative**:
```java
// Use BCrypt for passwords
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();
String hashedPassword = encoder.encode(password);
boolean matches = encoder.matches(password, hashedPassword);

// Or use Argon2
import org.springframework.security.crypto.argon2.Argon2PasswordEncoder;

Argon2PasswordEncoder encoder = new Argon2PasswordEncoder();
String hashedPassword = encoder.encode(password);

// Secure random
import java.security.SecureRandom;

SecureRandom random = new SecureRandom();
byte[] token = new byte[32];
random.nextBytes(token);

// Secure encryption (AES-GCM)
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

KeyGenerator keyGen = KeyGenerator.getInstance("AES");
keyGen.init(256);
SecretKey key = keyGen.generateKey();

Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
byte[] iv = new byte[12];
new SecureRandom().nextBytes(iv);
GCMParameterSpec spec = new GCMParameterSpec(128, iv);
cipher.init(Cipher.ENCRYPT_MODE, key, spec);
```

### 7. Spring Expression Language (SpEL) Injection
**Risk**: Remote code execution
**Detection Patterns**:
```java
// VULNERABLE - SpEL with user input
ExpressionParser parser = new SpelExpressionParser();
Expression exp = parser.parseExpression(userInput);
Object result = exp.getValue();

// VULNERABLE - @Value with user input
@Value("#{" + userInput + "}")
private String value;
```

**Secure Alternative**:
```java
// Don't use SpEL with user input
// Use simple property access instead
@Value("${app.property}")
private String value;

// If dynamic evaluation is needed, use whitelisting
Set<String> allowedExpressions = Set.of("property1", "property2");
if (!allowedExpressions.contains(userInput)) {
    throw new SecurityException("Invalid expression");
}
```

### 8. SSRF (Server-Side Request Forgery)
**Risk**: Internal network access
**Detection Patterns**:
```java
// VULNERABLE - Fetching user-provided URLs
String url = request.getParameter("url");
URL urlObj = new URL(url);
URLConnection conn = urlObj.openConnection();

// VULNERABLE - RestTemplate with user URL
RestTemplate restTemplate = new RestTemplate();
String response = restTemplate.getForObject(userUrl, String.class);
```

**Secure Alternative**:
```java
import java.net.InetAddress;
import java.net.URL;

public boolean isAllowedURL(String urlString) throws Exception {
    URL url = new URL(urlString);
    
    // Only allow HTTP/HTTPS
    if (!url.getProtocol().equals("http") && !url.getProtocol().equals("https")) {
        return false;
    }
    
    // Resolve hostname
    InetAddress address = InetAddress.getByName(url.getHost());
    
    // Block private IP ranges
    if (address.isSiteLocalAddress() || address.isLoopbackAddress()) {
        return false;
    }
    
    return true;
}

// Usage
if (!isAllowedURL(userUrl)) {
    throw new SecurityException("URL not allowed");
}
RestTemplate restTemplate = new RestTemplate();
String response = restTemplate.getForObject(userUrl, String.class);
```

## Spring Security Best Practices

### Authentication & Authorization
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf().csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
            .and()
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/public/**").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .formLogin()
            .and()
            .logout()
            .logoutSuccessUrl("/");
        
        return http.build();
    }
    
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
```

### Input Validation
```java
import javax.validation.constraints.*;

public class UserDTO {
    @NotBlank
    @Size(min = 3, max = 20)
    @Pattern(regexp = "^[a-zA-Z0-9_-]+$")
    private String username;
    
    @NotBlank
    @Email
    private String email;
    
    @NotBlank
    @Size(min = 8)
    private String password;
}

@RestController
public class UserController {
    @PostMapping("/users")
    public ResponseEntity<?> createUser(@Valid @RequestBody UserDTO userDTO) {
        // Validation happens automatically
        return ResponseEntity.ok(userService.create(userDTO));
    }
}
```

## Common Vulnerable Packages
**Check for CVEs**:
- `org.springframework:spring-core` < 6.0.14
- `com.fasterxml.jackson.core:jackson-databind` < 2.15.3
- `org.apache.commons:commons-text` < 1.10.0
- `log4j-core` < 2.17.1 (Log4Shell)
- `org.yaml:snakeyaml` < 2.0

## Security Checklist
- [ ] Deserialization prevention
- [ ] SQL injection prevention
- [ ] XXE prevention
- [ ] Path traversal prevention
- [ ] Command injection prevention
- [ ] Secure cryptography
- [ ] SSRF prevention
- [ ] Input validation
- [ ] Dependencies updated

## Advanced Java Security Discovery (Discovery Focus)

### 1. Fuzzing with Jazzer (Coverage-Guided)
**Methodology**: Fuzz Java parsing logic specifically.
*   **Technique**: Use `Jazzer` (based on libFuzzer).
*   **Action**:
    ```bash
    # Run jazzer on a strict parser class
    ./jazzer --cp=target/classes --target_class=com.example.XMLParser --autofuzz
    ```
*   **Target**: Fuzz classes that implement `Serializable`, `Externalizable`, or parse `JSON/XML`.

### 2. Deserialization Gadget Chain Discovery
**Methodology**: Detect classes that can be abused during `readObject()`.
*   **Technique**: Use `GadgetInspector` (static analysis).
*   **Manual**: Search for classes with `readObject` that invoke abstract methods/interfaces.
    ```java
    // Risky Pattern: Invoking a user-controlled object in readObject
    private void readObject(ObjectInputStream ois) {
        ois.defaultReadObject();
        ((Runnable) this.callback).run(); // CODE EXECUTION
    }
    ```

### 3. SpEL Injection Discovery
**Methodology**: Find places where user strings enter `ExpressionParser`.
*   **Audit**: Grep for `parseExpression(`.
*   **Trace**: Check if the argument comes from HTTP parameters.
*   **Payload**: `T(java.lang.Runtime).getRuntime().exec("id")`
*   **Zero Tolerance**: If ExpressionParser evaluates variable input, flag as **CRITICAL**.

### 4. Zero Tolerance Data Compromise Protocol
**Mandate**: Verify logger usage does not leak sensitive entities.
*   **Checks**:
    1.  **ToString()**: Check if `User` or `CreditCard` classes generate `toString()` with secrets.
    2.  **Log4j Config**: Ensure sensitive fields are masked in `PatternLayout`.
    3.  **Exception Handling**: Ensure `e.printStackTrace()` is never sent to `HttpServletResponse`.
```
"[package-name]" maven CVE vulnerability
"[package-name]" security advisory
"spring security best practices" 2024
mvn dependency-check [package-name]
```

## References
- [OWASP Java Security](https://owasp.org/www-project-proactive-controls/)
- [Spring Security](https://spring.io/projects/spring-security)
