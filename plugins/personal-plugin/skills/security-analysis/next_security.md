# Next.js Security Analysis

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

### 1. API Route Security
```javascript
// VULNERABLE - No authentication
// pages/api/users.js
export default async function handler(req, res) {
  const users = await db.users.findAll();
  res.json(users);  // Anyone can access
}

// SECURE - With authentication
import { getServerSession } from 'next-auth';
import { authOptions } from './auth/[...nextauth]';

export default async function handler(req, res) {
  const session = await getServerSession(req, res, authOptions);
  
  if (!session) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  
  // Check authorization
  if (session.user.role !== 'admin') {
    return res.status(403).json({ error: 'Forbidden' });
  }
  
  const users = await db.users.findAll();
  res.json(users);
}
```

### 2. Server-Side Injection
```javascript
// VULNERABLE - SQL injection in getServerSideProps
export async function getServerSideProps({ query }) {
  const user = await db.query(
    `SELECT * FROM users WHERE id = ${query.id}`  // SQL injection
  );
  return { props: { user } };
}

// SECURE - Parameterized queries
export async function getServerSideProps({ query }) {
  const user = await db.query(
    'SELECT * FROM users WHERE id = $1',
    [query.id]
  );
  return { props: { user } };
}
```

### 3. Sensitive Data in getServerSideProps
```javascript
// VULNERABLE - Exposing sensitive data
export async function getServerSideProps() {
  const user = await db.users.findOne({ id: userId });
  return {
    props: {
      user  // Includes password hash, tokens, etc.
    }
  };
}

// SECURE - Filter sensitive data
export async function getServerSideProps() {
  const user = await db.users.findOne({ id: userId });
  
  return {
    props: {
      user: {
        id: user.id,
        name: user.name,
        email: user.email
        // Exclude: password, tokens, etc.
      }
    }
  };
}
```

### 4. Missing CSRF Protection
```javascript
// VULNERABLE - No CSRF token
// pages/api/transfer.js
export default async function handler(req, res) {
  if (req.method === 'POST') {
    await transferMoney(req.body);
    res.json({ success: true });
  }
}

// SECURE - CSRF protection with next-csrf
import { createCsrfProtect } from '@edge-csrf/nextjs';

const csrfProtect = createCsrfProtect({
  cookie: {
    secure: process.env.NODE_ENV === 'production',
  },
});

export default async function handler(req, res) {
  await csrfProtect(req, res);
  
  if (req.method === 'POST') {
    await transferMoney(req.body);
    res.json({ success: true });
  }
}
```

### 5. Insecure Environment Variables
```javascript
// VULNERABLE - Exposing secrets to client
// next.config.js
module.exports = {
  env: {
    API_SECRET: process.env.API_SECRET,  // Exposed to client!
  }
};

// SECURE - Only expose NEXT_PUBLIC_ vars
module.exports = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,  // Safe
  }
};

// Server-side only
// pages/api/data.js
const API_SECRET = process.env.API_SECRET;  // Not exposed to client
```

### 6. XSS in Server-Rendered Content
```javascript
// VULNERABLE - dangerouslySetInnerHTML
export default function Page({ content }) {
  return <div dangerouslySetInnerHTML={{ __html: content }} />;
}

// SECURE - Sanitize HTML
import DOMPurify from 'isomorphic-dompurify';

export default function Page({ content }) {
  const sanitized = DOMPurify.sanitize(content);
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
}

// Better - Use markdown
import ReactMarkdown from 'react-markdown';

export default function Page({ content }) {
  return <ReactMarkdown>{content}</ReactMarkdown>;
}
```

### 7. Open Redirect
```javascript
// VULNERABLE - Unvalidated redirect
// pages/api/redirect.js
export default function handler(req, res) {
  const { url } = req.query;
  res.redirect(url);  // Can redirect anywhere
}

// SECURE - Validate redirect URLs
export default function handler(req, res) {
  const { url } = req.query;
  const allowedDomains = ['yourdomain.com', 'app.yourdomain.com'];
  
  try {
    const parsedUrl = new URL(url);
    if (allowedDomains.includes(parsedUrl.hostname)) {
      res.redirect(url);
    } else {
      res.status(400).json({ error: 'Invalid redirect URL' });
    }
  } catch {
    res.status(400).json({ error: 'Invalid URL' });
  }
}
```

### 8. Rate Limiting
```javascript
// Implement rate limiting for API routes
import rateLimit from 'express-rate-limit';
import slowDown from 'express-slow-down';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
});

const speedLimiter = slowDown({
  windowMs: 15 * 60 * 1000,
  delayAfter: 50,
  delayMs: 500,
});

export default function handler(req, res) {
  limiter(req, res, () => {
    speedLimiter(req, res, () => {
      // Your API logic
    });
  });
}
```

## Next.js 13+ App Router Security

### Server Actions Security
```typescript
// app/actions.ts
'use server'

import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { z } from 'zod';

const schema = z.object({
  email: z.string().email(),
  name: z.string().min(3),
});

export async function createUser(formData: FormData) {
  // Validate input
  const validatedFields = schema.safeParse({
    email: formData.get('email'),
    name: formData.get('name'),
  });

  if (!validatedFields.success) {
    return {
      errors: validatedFields.error.flatten().fieldErrors,
    };
  }

  // Check authentication
  const session = await getServerSession();
  if (!session) {
    redirect('/login');
  }

  // Process data
  await db.users.create(validatedFields.data);
  revalidatePath('/users');
}
```

### Middleware Security
```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Security headers
  const response = NextResponse.next();
  
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set(
    'Content-Security-Policy',
    "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval';"
  );
  
  // Authentication check
  const token = request.cookies.get('token');
  if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
  
  return response;
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

## Security Headers Configuration

```javascript
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
        ],
      },
    ];
  },
};
```

## Common Vulnerable Packages
- `next` < 14.0.4
- `next-auth` < 4.24.5
- `axios` < 1.6.0

## Security Checklist
- [ ] API routes have authentication
- [ ] Server-side injection prevention
- [ ] No sensitive data in props
- [ ] CSRF protection
- [ ] Environment variables properly scoped
- [ ] XSS prevention
- [ ] Open redirect prevention
- [ ] Rate limiting
- [ ] Security headers configured

## Advanced Next.js Security Discovery (Discovery Focus)

### 1. Server Action Fuzzing (React Server Components)
**Methodology**: Server Actions are public API endpoints even if not documented.
*   **Audit**: Grep for `'use server'`. every export is a public endpoint.
*   **Test**: Are there arguments that are complex objects?
*   **Fuzz**: Invoke the action (via `fetch` to the hashed endpoint id if possible, or by replaying the POST request) with unexpected types.
*   **Zero Tolerance**: If a Server Action takes `userId` as an argument without checking `session.user.id`, flag as **CRITICAL IDOR**.

### 2. Middleware Bypass Detection
**Methodology**: Next.js Middleware regex matchers can be tricky.
*   **Audit**: Check `matcher` in `middleware.ts`.
*   **Bypass**: Can you access `/api/admin` via `/API/ADMIN`? Or `/_next/../api/admin`?
*   **Test**: Fuzz UUID paths and casing to see if middleware logic is skipped.

### 3. ISR / Cache Poisoning
**Methodology**: manipulating headers to poison the cache for other users.
*   **Audit**: Check usages of `revalidateTag` or `revalidatePath` triggered by user input.
*   **Risk**: If a user can trigger a revalidation with malicious content that gets cached for everyone.

### 4. Zero Tolerance Data Compromise Protocol
**Mandate**: Secrets in Client Bundles.
*   **Check**:
    1.  Grep `.next/static/chunks` for `SECRET_KEY`, `API_KEY`.
    2.  Ensure `NEXT_PUBLIC_` is ONLY used for non-sensitive data.
    3.  Flag any `process.env` usage in client components that is not prefixed with `NEXT_PUBLIC_` (it won't be replaced, but might be leaking code intent).

## References
- [Next.js Security](https://nextjs.org/docs/advanced-features/security-headers)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
