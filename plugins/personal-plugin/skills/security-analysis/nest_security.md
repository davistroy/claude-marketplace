# NestJS Security Analysis

## Overview
NestJS applications built on Express/Fastify face security challenges from TypeScript/JavaScript vulnerabilities, dependency issues, and framework-specific patterns. This guide provides comprehensive security analysis for NestJS.

## Critical Vulnerability Patterns

### 1. SQL/NoSQL Injection
**Risk**: Database compromise
**Detection Patterns**:
```typescript
// VULNERABLE - Raw queries with string interpolation
@Get(':id')
async getUser(@Param('id') id: string) {
  return this.userRepository.query(
    `SELECT * FROM users WHERE id = ${id}` // SQL injection
  );
}

// VULNERABLE - TypeORM raw query
@Get('search')
async search(@Query('name') name: string) {
  return this.userRepository.query(
    `SELECT * FROM users WHERE name = '${name}'`
  );
}

// VULNERABLE - Mongoose query injection
@Get('find')
async find(@Query() query: any) {
  return this.userModel.find(query); // Can inject { $ne: null }
}
```

**Secure Alternative**:
```typescript
// Use parameterized queries
@Get(':id')
async getUser(@Param('id', ParseIntPipe) id: number) {
  return this.userRepository.query(
    'SELECT * FROM users WHERE id = $1',
    [id]
  );
}

// Use ORM methods
@Get('search')
async search(@Query('name') name: string) {
  return this.userRepository.findOne({ where: { name } });
}

// Validate and sanitize Mongoose queries
import { IsString, IsNotEmpty } from 'class-validator';

class SearchDto {
  @IsString()
  @IsNotEmpty()
  name: string;
}

@Get('find')
async find(@Query() query: SearchDto) {
  return this.userModel.findOne({ name: query.name });
}
```

### 2. Missing Authentication/Authorization
**Risk**: Unauthorized access to resources
**Detection Patterns**:
```typescript
// VULNERABLE - No authentication
@Get('admin/users')
async getAllUsers() {
  return this.userService.findAll();
}

// VULNERABLE - No authorization check
@Delete(':id')
async deleteUser(@Param('id') id: string) {
  return this.userService.delete(id);
}

// VULNERABLE - Client-side role check only
@Get('admin')
async adminPanel(@Request() req) {
  // No server-side validation
  return this.adminService.getData();
}
```

**Secure Alternative**:
```typescript
// Use Guards for authentication
import { UseGuards } from '@nestjs/common';
import { JwtAuthGuard } from './guards/jwt-auth.guard';
import { RolesGuard } from './guards/roles.guard';
import { Roles } from './decorators/roles.decorator';

@UseGuards(JwtAuthGuard, RolesGuard)
@Roles('admin')
@Get('admin/users')
async getAllUsers() {
  return this.userService.findAll();
}

// Verify ownership
@UseGuards(JwtAuthGuard)
@Delete(':id')
async deleteUser(
  @Param('id', ParseIntPipe) id: number,
  @Request() req
) {
  const user = await this.userService.findOne(id);
  if (user.id !== req.user.id && !req.user.isAdmin) {
    throw new ForbiddenException();
  }
  return this.userService.delete(id);
}

// RolesGuard implementation
@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredRoles = this.reflector.get<string[]>(
      'roles',
      context.getHandler()
    );
    if (!requiredRoles) return true;

    const { user } = context.switchToHttp().getRequest();
    return requiredRoles.some((role) => user.roles?.includes(role));
  }
}
```

### 3. Missing Input Validation
**Risk**: Injection attacks, business logic bypass
**Detection Patterns**:
```typescript
// VULNERABLE - No validation
@Post('create')
async create(@Body() data: any) {
  return this.userService.create(data);
}

// VULNERABLE - Partial validation
@Post('update')
async update(@Body() data: { name: string }) {
  return this.userService.update(data); // Other fields not validated
}

// VULNERABLE - No sanitization
@Post('comment')
async createComment(@Body('text') text: string) {
  return this.commentService.create(text); // XSS risk
}
```

**Secure Alternative**:
```typescript
// Use DTOs with class-validator
import { 
  IsString, 
  IsEmail, 
  IsInt, 
  Min, 
  Max, 
  Length,
  Matches 
} from 'class-validator';
import { Transform } from 'class-transformer';
import * as sanitizeHtml from 'sanitize-html';

export class CreateUserDto {
  @IsString()
  @Length(2, 50)
  @Matches(/^[a-zA-Z0-9_-]+$/)
  username: string;

  @IsEmail()
  email: string;

  @IsInt()
  @Min(18)
  @Max(120)
  age: number;

  @IsString()
  @Transform(({ value }) => sanitizeHtml(value))
  bio: string;
}

@Post('create')
async create(@Body() createUserDto: CreateUserDto) {
  return this.userService.create(createUserDto);
}

// Enable global validation
// main.ts
app.useGlobalPipes(new ValidationPipe({
  whitelist: true, // Strip non-whitelisted properties
  forbidNonWhitelisted: true, // Throw error on non-whitelisted
  transform: true, // Auto-transform to DTO types
}));
```

### 4. Insecure JWT Configuration
**Risk**: Token forgery, session hijacking
**Detection Patterns**:
```typescript
// VULNERABLE - Weak secret
JwtModule.register({
  secret: 'secret123',
  signOptions: { expiresIn: '7d' }
})

// VULNERABLE - No expiration
JwtModule.register({
  secret: process.env.JWT_SECRET
  // No expiresIn
})

// VULNERABLE - Algorithm not specified
this.jwtService.verify(token); // Accepts any algorithm
```

**Secure Alternative**:
```typescript
// Use strong secret from environment
JwtModule.register({
  secret: process.env.JWT_SECRET, // Min 256 bits
  signOptions: { 
    expiresIn: '15m', // Short-lived access tokens
    algorithm: 'HS256'
  }
})

// Implement refresh tokens
@Injectable()
export class AuthService {
  async login(user: User) {
    const payload = { sub: user.id, username: user.username };
    
    return {
      access_token: this.jwtService.sign(payload, {
        expiresIn: '15m'
      }),
      refresh_token: this.jwtService.sign(payload, {
        expiresIn: '7d',
        secret: process.env.JWT_REFRESH_SECRET
      })
    };
  }

  async refresh(refreshToken: string) {
    try {
      const payload = this.jwtService.verify(refreshToken, {
        secret: process.env.JWT_REFRESH_SECRET,
        algorithms: ['HS256']
      });
      
      return {
        access_token: this.jwtService.sign({
          sub: payload.sub,
          username: payload.username
        })
      };
    } catch {
      throw new UnauthorizedException();
    }
  }
}
```

### 5. CORS Misconfiguration
**Risk**: Unauthorized cross-origin requests
**Detection Patterns**:
```typescript
// VULNERABLE - Allow all origins
app.enableCors({
  origin: '*'
});

// VULNERABLE - Credentials with wildcard
app.enableCors({
  origin: '*',
  credentials: true // Invalid combination
});

// VULNERABLE - Regex too permissive
app.enableCors({
  origin: /\.com$/ // Matches any .com domain
});
```

**Secure Alternative**:
```typescript
// Specific origins
app.enableCors({
  origin: ['https://yourdomain.com', 'https://app.yourdomain.com'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  maxAge: 3600
});

// Dynamic origin validation
app.enableCors({
  origin: (origin, callback) => {
    const allowedOrigins = process.env.ALLOWED_ORIGINS.split(',');
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true
});
```

### 6. Missing Rate Limiting
**Risk**: Brute force, DoS attacks
**Detection Patterns**:
```typescript
// VULNERABLE - No rate limiting on auth
@Post('login')
async login(@Body() credentials: LoginDto) {
  return this.authService.login(credentials);
}

// VULNERABLE - No rate limiting on expensive operations
@Get('export')
async exportData() {
  return this.dataService.exportAll(); // Resource intensive
}
```

**Secure Alternative**:
```typescript
// Install @nestjs/throttler
import { ThrottlerGuard, ThrottlerModule } from '@nestjs/throttler';

// Configure globally
@Module({
  imports: [
    ThrottlerModule.forRoot({
      ttl: 60,
      limit: 10,
    }),
  ],
})
export class AppModule {}

// Apply globally
app.useGlobalGuards(new ThrottlerGuard());

// Custom rate limit for specific endpoints
import { Throttle } from '@nestjs/throttler';

@Throttle(5, 60) // 5 requests per 60 seconds
@Post('login')
async login(@Body() credentials: LoginDto) {
  return this.authService.login(credentials);
}

// Skip rate limiting for certain routes
import { SkipThrottle } from '@nestjs/throttler';

@SkipThrottle()
@Get('public')
async publicData() {
  return this.dataService.getPublic();
}
```

### 7. Insecure File Upload
**Risk**: Malicious file execution, path traversal
**Detection Patterns**:
```typescript
// VULNERABLE - No file type validation
@Post('upload')
@UseInterceptors(FileInterceptor('file'))
async upload(@UploadedFile() file: Express.Multer.File) {
  return this.fileService.save(file);
}

// VULNERABLE - No size limit
@Post('upload')
@UseInterceptors(FileInterceptor('file'))
async upload(@UploadedFile() file: Express.Multer.File) {
  // No size check
}
```

**Secure Alternative**:
```typescript
import { diskStorage } from 'multer';
import { extname } from 'path';
import { v4 as uuid } from 'uuid';

@Post('upload')
@UseInterceptors(
  FileInterceptor('file', {
    storage: diskStorage({
      destination: './uploads',
      filename: (req, file, cb) => {
        // Generate unique filename
        const uniqueName = `${uuid()}${extname(file.originalname)}`;
        cb(null, uniqueName);
      },
    }),
    fileFilter: (req, file, cb) => {
      // Validate file type
      const allowedMimes = ['image/jpeg', 'image/png', 'image/gif'];
      if (allowedMimes.includes(file.mimetype)) {
        cb(null, true);
      } else {
        cb(new BadRequestException('Invalid file type'), false);
      }
    },
    limits: {
      fileSize: 5 * 1024 * 1024, // 5MB
    },
  })
)
async upload(@UploadedFile() file: Express.Multer.File) {
  // Additional validation
  if (!file) {
    throw new BadRequestException('No file uploaded');
  }
  
  return {
    filename: file.filename,
    size: file.size,
    mimetype: file.mimetype
  };
}
```

### 8. Information Disclosure
**Risk**: Sensitive data leakage
**Detection Patterns**:
```typescript
// VULNERABLE - Returning full user object
@Get('profile')
async getProfile(@Request() req) {
  return this.userService.findOne(req.user.id); // Includes password hash
}

// VULNERABLE - Detailed error messages
@Get(':id')
async getUser(@Param('id') id: string) {
  try {
    return await this.userService.findOne(id);
  } catch (error) {
    throw new HttpException(error.message, 500); // Leaks stack trace
  }
}
```

**Secure Alternative**:
```typescript
// Use serialization to exclude sensitive fields
import { Exclude } from 'class-transformer';

export class User {
  id: number;
  username: string;
  email: string;
  
  @Exclude()
  password: string;
  
  @Exclude()
  resetToken: string;
}

// Enable serialization
app.useGlobalInterceptors(
  new ClassSerializerInterceptor(app.get(Reflector))
);

// Generic error messages
@Get(':id')
async getUser(@Param('id', ParseIntPipe) id: number) {
  try {
    const user = await this.userService.findOne(id);
    if (!user) {
      throw new NotFoundException('User not found');
    }
    return user;
  } catch (error) {
    if (error instanceof NotFoundException) {
      throw error;
    }
    // Log detailed error server-side
    this.logger.error(error);
    // Return generic message to client
    throw new InternalServerErrorException('An error occurred');
  }
}
```

## Security Best Practices

### Global Security Configuration
```typescript
// main.ts
import helmet from 'helmet';
import * as csurf from 'csurf';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Security headers
  app.use(helmet());

  // CSRF protection
  app.use(csurf());

  // CORS
  app.enableCors({
    origin: process.env.ALLOWED_ORIGINS.split(','),
    credentials: true
  });

  // Global validation
  app.useGlobalPipes(new ValidationPipe({
    whitelist: true,
    forbidNonWhitelisted: true,
    transform: true
  }));

  // Global rate limiting
  app.useGlobalGuards(new ThrottlerGuard());

  // Serialization
  app.useGlobalInterceptors(
    new ClassSerializerInterceptor(app.get(Reflector))
  );

  await app.listen(3000);
}
```

## Common Vulnerable Packages
- `@nestjs/jwt` < 10.0.0
- `@nestjs/passport` < 9.0.0
- `class-validator` < 0.14.0
- `typeorm` < 0.3.17
- `mongoose` < 7.0.0

## Security Checklist
- [ ] Authentication guards on protected routes
- [ ] Authorization checks for resource access
- [ ] Input validation with DTOs
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] JWT with strong secrets and expiration
- [ ] File upload validation
- [ ] Error handling doesn't leak info
- [ ] Dependencies updated regularly

## Advanced NestJS Security Discovery (Discovery Focus)

### 1. Decorator Security Analysis
**Methodology**: Checking if guards are actually applied to controllers/methods.
*   **Audit**: Manual or regex check for public endpoints.
    *   Find all `@Controller` and `@Get/@Post`.
    *   Verify `@UseGuards` or `@Auth` decorator exists.
*   **Zero Tolerance**: Any endpoint exposing `@Post` without a Guard or `@Public()` explicit tag is **CRITICAL**.

### 2. Custom Validator Fuzzing
**Methodology**: `class-validator` custom decorators often fail to handle non-string inputs safely.
*   **Audit**: Grep for `@ValidatorConstraint`.
*   **Fuzz**: Pass `numbers`, `arrays`, and `null` to fields expecting `strings` in custom validators.
*   **Pattern**:
    ```typescript
    validate(text: string) { return text.includes('foo'); } // CRASH if text is number
    ```

### 3. Dependency Injection Graph Manipulation
**Methodology**: Ensure `Scope.REQUEST` providers don't cache sensitive data.
*   **Audit**: Grep for `{ scope: Scope.REQUEST }`.
*   **Risk**: If a singleton service injects a request-scoped service, it might hold onto user data effectively executing a "Cross-User Data Leak".
*   **Check**: Verify usage of `REQUEST` scoped providers.

### 4. Zero Tolerance Data Compromise Protocol
**Mandate**: Interceptors must not mutate Exceptions to leak details.
*   **Check**:
    1.  Review `ExceptionFilter`.
    2.  Ensure `exception.stack` is never assigned to the `response` body.
    3.  Verify that `ClassSerializerInterceptor` is globally enabled (`app.useGlobalInterceptors`).

## References
- [NestJS Security](https://docs.nestjs.com/security/authentication)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
