# Vue.js Security Analysis

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

### 1. XSS via v-html
```vue
<!-- VULNERABLE -->
<div v-html="userInput"></div>

<!-- SECURE -->
<div>{{ userInput }}</div>  <!-- Auto-escaped -->

<!-- If HTML is needed, sanitize first -->
<template>
  <div v-html="sanitizedHtml"></div>
</template>

<script>
import DOMPurify from 'dompurify';

export default {
  computed: {
    sanitizedHtml() {
      return DOMPurify.sanitize(this.userInput);
    }
  }
}
</script>
```

### 2. Template Injection
```vue
<!-- VULNERABLE -->
<component :is="userInput"></component>

<!-- SECURE - Whitelist components -->
<component :is="allowedComponent"></component>

<script>
export default {
  computed: {
    allowedComponent() {
      const allowed = ['ComponentA', 'ComponentB'];
      return allowed.includes(this.userInput) ? this.userInput : 'DefaultComponent';
    }
  }
}
</script>
```

### 3. Sensitive Data in Vuex Store
```javascript
// VULNERABLE - Storing sensitive data
const store = new Vuex.Store({
  state: {
    user: {
      password: 'secret123',  // Never store passwords
      creditCard: '1234-5678'  // Never store in frontend
    }
  }
});

// SECURE - Only store non-sensitive data
const store = new Vuex.Store({
  state: {
    user: {
      id: 123,
      name: 'John Doe',
      email: 'john@example.com'
      // No passwords, tokens, or PII
    }
  }
});
```

### 4. Insecure API Calls
```javascript
// VULNERABLE - API keys in frontend
const API_KEY = 'sk_live_abc123';
axios.get(`https://api.example.com/data?key=${API_KEY}`);

// SECURE - Use backend proxy
axios.get('/api/data'); // Backend adds API key
```

### 5. Missing CSRF Protection
```vue
<!-- VULNERABLE -->
<form @submit="submitForm">
  <input v-model="formData.name">
  <button type="submit">Submit</button>
</form>

<!-- SECURE - Include CSRF token -->
<form @submit="submitForm">
  <input type="hidden" name="_csrf" :value="csrfToken">
  <input v-model="formData.name">
  <button type="submit">Submit</button>
</form>

<script>
export default {
  data() {
    return {
      csrfToken: document.querySelector('meta[name="csrf-token"]').content
    }
  },
  methods: {
    submitForm() {
      axios.post('/api/submit', {
        ...this.formData,
        _csrf: this.csrfToken
      });
    }
  }
}
</script>
```

## Vue 3 Composition API Security

```vue
<script setup>
import { ref, computed } from 'vue';
import DOMPurify from 'dompurify';

const userInput = ref('');

// Sanitize HTML
const sanitizedHtml = computed(() => {
  return DOMPurify.sanitize(userInput.value);
});

// Validate input
const isValidEmail = computed(() => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(userInput.value);
});
</script>
```

## Common Vulnerable Packages
- `vue` < 3.3.8
- `vue-router` < 4.2.5
- `vuex` < 4.1.0
- `axios` < 1.6.0

## Security Checklist
- [ ] XSS prevention (avoid v-html)
- [ ] CSRF protection
- [ ] No sensitive data in store
- [ ] API keys not in frontend
- [ ] Input validation
- [ ] Dependencies updated

## Advanced Vue.js Security Discovery (Discovery Focus)

### 1. Vuex / Pinia State Manipulation
**Methodology**: Modify state in DevTools to bypass client-side logic.
*   **Technique**: Open Vue DevTools -> Pinia/Vuex.
*   **Action**:
    1.  Locate `user.permissions` or `auth.isAuthenticated`.
    2.  Mutate value to `['admin']` or `true`.
    3.  Attempt restricted action.
    4.  **Zero Tolerance**: If backend relies on this state without verifying the token/session again, flag as **CRITICAL**.

### 2. Component Prop Fuzzing
**Methodology**: Inject malicious types into component props.
*   **Audit**: Check `props` definition.
*   **Fuzz**: If prop expects `String`, pass `Object` or `Array` via parent component.
*   **Risk**: Logic that assumes string methods (`.split`, `.replace`) will crash (DoS) or behave unexpectedly.

### 3. Server-Side Rendering (Nuxt) Injection
**Methodology**: SSR hydration mismatch or injection.
*   **Audit**: Check `useAsyncData` or `fetch` hooks.
*   **Payload**: `"><img src=x onerror=alert(1)>`.
*   **Check**: If the payload is rendered in the initial HTML (view-source) unescaped, it's an XSS vector.

### 4. Zero Tolerance Data Compromise Protocol
**Mandate**: No reactive leakage.
*   **Check**:
    1.  Ensure `v-html` is NEVER used with user input, even if "sanitized" (unless strictly audited).
    2.  Check `watcheffect` or `computed` properties for side effects that log sensitive data.

## References
- [Vue.js Security](https://vuejs.org/guide/best-practices/security.html)
- [OWASP Frontend Security](https://owasp.org/www-project-web-security-testing-guide/)
