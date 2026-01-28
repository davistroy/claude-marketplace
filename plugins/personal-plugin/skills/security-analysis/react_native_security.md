# React Native Security Analysis

## Dependency Scanning Commands

```bash
# npm audit
npm audit
npm audit fix

# Check for outdated packages
npm outdated

# Snyk scan
npx snyk test
```

## Critical Vulnerability Patterns

### 1. Insecure Storage
```javascript
// VULNERABLE - Storing sensitive data in AsyncStorage
import AsyncStorage from '@react-native-async-storage/async-storage';

await AsyncStorage.setItem('authToken', token);  // Unencrypted
await AsyncStorage.setItem('password', password);  // Never store passwords

// SECURE - Use encrypted storage
import * as SecureStore from 'expo-secure-store';
// or
import EncryptedStorage from 'react-native-encrypted-storage';

await SecureStore.setItemAsync('authToken', token);  // Encrypted

// For sensitive data
await EncryptedStorage.setItem('user_session', JSON.stringify({
  token: authToken,
  refreshToken: refreshToken
}));
```

### 2. Hardcoded API Keys
```javascript
// VULNERABLE
const API_KEY = 'sk_live_abc123';
const API_URL = 'https://api.example.com';

// SECURE - Use environment variables
import Config from 'react-native-config';

const API_KEY = Config.API_KEY;
const API_URL = Config.API_URL;

// .env file (not committed to git)
// API_KEY=your_key_here
// API_URL=https://api.example.com
```

### 3. Insecure Deep Linking
```javascript
// VULNERABLE - No validation
Linking.addEventListener('url', ({ url }) => {
  const route = url.replace(/.*?:\/\//g, '');
  navigation.navigate(route);  // Can navigate anywhere
});

// SECURE - Validate deep links
Linking.addEventListener('url', ({ url }) => {
  const allowedRoutes = ['home', 'profile', 'settings'];
  const route = url.replace(/.*?:\/\//g, '');
  
  if (allowedRoutes.includes(route)) {
    navigation.navigate(route);
  } else {
    console.warn('Invalid deep link:', url);
  }
});
```

### 4. Missing Certificate Pinning
```javascript
// VULNERABLE - No certificate pinning
fetch('https://api.example.com/data');

// SECURE - Implement certificate pinning
// Using react-native-ssl-pinning
import { fetch as sslFetch } from 'react-native-ssl-pinning';

sslFetch('https://api.example.com/data', {
  method: 'GET',
  sslPinning: {
    certs: ['cert1', 'cert2']  // Your certificate hashes
  }
});
```

### 5. Weak Cryptography
```javascript
// VULNERABLE - Base64 is not encryption
const encoded = btoa(sensitiveData);

// SECURE - Use proper encryption
import CryptoJS from 'crypto-js';

const encrypted = CryptoJS.AES.encrypt(
  sensitiveData,
  encryptionKey
).toString();

const decrypted = CryptoJS.AES.decrypt(
  encrypted,
  encryptionKey
).toString(CryptoJS.enc.Utf8);
```

### 6. Jailbreak/Root Detection
```javascript
// Implement jailbreak/root detection
import JailMonkey from 'jail-monkey';

if (JailMonkey.isJailBroken()) {
  Alert.alert(
    'Security Warning',
    'This app cannot run on jailbroken devices'
  );
  // Exit or limit functionality
}

// Check for debugging
if (JailMonkey.isDebuggedMode()) {
  // Handle debugging detection
}
```

### 7. Insecure WebView
```javascript
// VULNERABLE
import { WebView } from 'react-native-webview';

<WebView
  source={{ uri: userProvidedUrl }}
  javaScriptEnabled={true}
/>

// SECURE
<WebView
  source={{ uri: trustedUrl }}
  javaScriptEnabled={false}  // Disable if not needed
  originWhitelist={['https://*']}
  onShouldStartLoadWithRequest={(request) => {
    // Validate URLs before loading
    return request.url.startsWith('https://trusted-domain.com');
  }}
/>
```

### 8. Logging Sensitive Data
```javascript
// VULNERABLE
console.log('User password:', password);
console.log('Auth token:', authToken);

// SECURE
// Remove console.log in production
if (__DEV__) {
  console.log('Debug info:', nonSensitiveData);
}

// Use proper logging library
import { logger } from './utils/logger';
logger.info('User logged in', { userId: user.id });  // No sensitive data
```

## Security Best Practices

### Secure API Communication
```javascript
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

const api = axios.create({
  baseURL: Config.API_URL,
  timeout: 10000,
});

// Add auth token from secure storage
api.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Refresh token logic
      const refreshToken = await SecureStore.getItemAsync('refreshToken');
      // ... refresh logic
    }
    return Promise.reject(error);
  }
);
```

### Biometric Authentication
```javascript
import * as LocalAuthentication from 'expo-local-authentication';

const authenticateWithBiometrics = async () => {
  const hasHardware = await LocalAuthentication.hasHardwareAsync();
  const isEnrolled = await LocalAuthentication.isEnrolledAsync();
  
  if (hasHardware && isEnrolled) {
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: 'Authenticate to continue',
      fallbackLabel: 'Use passcode',
    });
    
    return result.success;
  }
  
  return false;
};
```

### Code Obfuscation
```bash
# Install react-native-obfuscating-transformer
npm install --save-dev react-native-obfuscating-transformer

# metro.config.js
module.exports = {
  transformer: {
    babelTransformerPath: require.resolve('react-native-obfuscating-transformer')
  }
};
```

## Common Vulnerable Packages
- `react-native` < 0.72.7
- `@react-native-async-storage/async-storage` < 1.19.5
- `react-native-webview` < 13.6.2
- `axios` < 1.6.0

## Security Checklist
- [ ] Sensitive data in encrypted storage
- [ ] No hardcoded secrets
- [ ] Certificate pinning implemented
- [ ] Deep link validation
- [ ] Jailbreak/root detection
- [ ] Secure WebView configuration
- [ ] No sensitive data in logs
- [ ] Biometric authentication
- [ ] Code obfuscation for production

## Advanced React Native Security Discovery (Discovery Focus)

### 1. Deep Link Fuzzing
**Methodology**: `Linking.getInitialURL` is an unauthenticated entry point.
*   **Technique**: Use `adb` to fire intents.
    ```bash
    adb shell am start -W -a android.intent.action.VIEW -d "myapp://admin/reset-password"
    ```
*   **Action**: Fuzz parameters in the URL scheme.
    *   `myapp://webview?url=javascript:alert(1)` (XSS in WebView)
    *   `myapp://profile?id=../` (Path Traversal logic)

### 2. Local Storage Forensics
**Methodology**: Dump app data from a rooted device/emulator.
*   **Audit**:
    1.  `adb shell run-as com.myapp ls /data/data/com.myapp/shared_prefs/`
    2.  Check for `AsyncStorage` implementations (usually SQLite or XML).
    3.  **Zero Tolerance**: If `grep -r "ey..."` (JWT) finds a valid token in plain text XML/SQLite, flag as **CRITICAL**.

### 3. Bridge Injection Discovery
**Methodology**: React Native Bridge allows JS to call Native modules.
*   **Audit**: Check custom Native Modules (`@ReactMethod`).
*   **Risk**: If a `String` argument passed from JS is used in `Runtime.exec()` or SQL on the native side without validation.
*   **Fuzz**: Pass null bytes `%00` or huge strings to native methods from JS.

### 4. Zero Tolerance Data Compromise Protocol
**Mandate**: No sensitive data in Logcat/XCode Logs.
*   **Check**:
    1.  Connect device, run `adb logcat | grep "token"`.
    2.  Check for Redux Logger middleware enabled in production.
    3.  Verify Screenshots/Snapshots (Task Switcher) do not show sensitive screens (use `react-native-privacy-snapshot`).

## References
- [OWASP Mobile Security](https://owasp.org/www-project-mobile-security/)
- [React Native Security](https://reactnative.dev/docs/security)
