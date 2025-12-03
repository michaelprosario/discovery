# Firebase Authentication Frontend Specification - DiscoveryPortal

## Overview

This document specifies the implementation of Firebase Authentication for the DiscoveryPortal Angular application. The implementation will integrate with the Firebase-protected backend API, manage user sessions, and provide a seamless authentication experience.

**Created:** December 3, 2025  
**Status:** Draft  
**Repository:** michaelprosario/discovery  
**Project:** discoveryPortal (Angular 21)  
**Related:** `prompts/firebase_login_backend_spec.md`

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Firebase Authentication Architecture](#firebase-authentication-architecture)
3. [Authentication Flow](#authentication-flow)
4. [Implementation Strategy](#implementation-strategy)
5. [Service Layer Implementation](#service-layer-implementation)
6. [HTTP Interceptor Implementation](#http-interceptor-implementation)
7. [UI Components](#ui-components)
8. [Route Guards](#route-guards)
9. [State Management](#state-management)
10. [Error Handling](#error-handling)
11. [Testing Requirements](#testing-requirements)
12. [Implementation Checklist](#implementation-checklist)

---

## Current State Analysis

### Application Structure

**Framework:** Angular 21.0.0  
**Build System:** Angular CLI  
**HTTP Client:** `@angular/common/http`  
**Routing:** `@angular/router`  
**State:** Component-based (no NgRx/Akita)

### Current Architecture

**Infrastructure Layer:** `src/app/infrastructure/`
- `config/api-config.service.ts` - API base URL configuration
- `http/http-client.service.ts` - Base HTTP client with error handling
- `http/*-api.service.ts` - Feature-specific API services (notebook, source, output, etc.)

**Core Layer:** `src/app/core/`
- `models/` - Data transfer objects and domain models
- `interfaces/` - TypeScript interfaces
- `services/` - Currently empty (business logic services)

**Component Layer:** `src/app/`
- Feature components: `notebook-list/`, `chat/`, `generate-blog-post/`, etc.
- Shared components: `shared/`, `side-menu/`
- Layout: `app.ts`, `app.html`

### Current HTTP Flow

```typescript
// No authentication currently implemented
HttpClientService → HttpClient → Backend API
```

**Gaps Identified:**
1. ❌ No authentication service
2. ❌ No HTTP interceptor for tokens
3. ❌ No route guards
4. ❌ No login/logout UI
5. ❌ No user state management
6. ❌ No token refresh mechanism
7. ❌ No 401/403 error handling

---

## Firebase Authentication Architecture

### Firebase Integration Approach

**Firebase Package:** `@angular/fire` (AngularFire)  
**Version:** Latest compatible with Angular 21  
**Authentication Module:** `@angular/fire/auth`

**Alternative:** Firebase JavaScript SDK (if AngularFire not compatible)
- `firebase/app`
- `firebase/auth`

### Key Responsibilities

1. **User Authentication:**
   - Email/password login
   - Google OAuth (optional future enhancement)
   - Session persistence
   - Automatic token refresh

2. **Token Management:**
   - Retrieve ID tokens from Firebase
   - Attach tokens to API requests
   - Handle token expiration
   - Clear tokens on logout

3. **User State:**
   - Track authentication status
   - Store user profile (email, display name)
   - Provide user observable for reactive components

4. **Security:**
   - Secure token storage
   - HTTPS-only cookies (if using cookie storage)
   - XSS protection via Angular sanitization

---

## Authentication Flow

### User Login Flow

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐         ┌──────────────┐
│   User      │         │  Angular App │         │  Firebase   │         │   Backend    │
│  Browser    │         │              │         │   Auth      │         │   API        │
└──────┬──────┘         └──────┬───────┘         └──────┬──────┘         └──────┬───────┘
       │                       │                        │                        │
       │ 1. Enter credentials  │                        │                        │
       ├──────────────────────>│                        │                        │
       │                       │                        │                        │
       │                       │ 2. Sign in with        │                        │
       │                       │    Firebase Auth       │                        │
       │                       ├───────────────────────>│                        │
       │                       │                        │                        │
       │                       │ 3. User Credential     │                        │
       │                       │    (ID Token)          │                        │
       │                       │<───────────────────────┤                        │
       │                       │                        │                        │
       │                       │ 4. Store user state    │                        │
       │                       │    and token           │                        │
       │                       │                        │                        │
       │ 5. Redirect to app    │                        │                        │
       │<──────────────────────┤                        │                        │
       │                       │                        │                        │
       │ 6. Make API request   │                        │                        │
       ├──────────────────────>│                        │                        │
       │                       │                        │                        │
       │                       │ 7. Get current token   │                        │
       │                       ├───────────────────────>│                        │
       │                       │                        │                        │
       │                       │ 8. Fresh ID token      │                        │
       │                       │<───────────────────────┤                        │
       │                       │                        │                        │
       │                       │ 9. API request with    │                        │
       │                       │    Bearer token        │                        │
       │                       ├───────────────────────────────────────────────>│
       │                       │                        │                        │
       │                       │ 10. Authorized response│                        │
       │                       │<───────────────────────────────────────────────┤
       │                       │                        │                        │
       │ 11. Display data      │                        │                        │
       │<──────────────────────┤                        │                        │
```

### Token Refresh Flow

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  HTTP       │         │  Auth        │         │  Firebase   │
│  Interceptor│         │  Service     │         │   Auth      │
└──────┬──────┘         └──────┬───────┘         └──────┬──────┘
       │                       │                        │
       │ 1. Intercept request  │                        │
       ├──────────────────────>│                        │
       │                       │                        │
       │                       │ 2. Get ID token        │
       │                       │    (auto-refresh if    │
       │                       │     expired)           │
       │                       ├───────────────────────>│
       │                       │                        │
       │                       │ 3. Fresh token         │
       │                       │<───────────────────────┤
       │                       │                        │
       │ 4. Token for header   │                        │
       │<──────────────────────┤                        │
       │                       │                        │
       │ 5. Request with       │                        │
       │    Authorization      │                        │
       │    header             │                        │
```

### Session Persistence

Firebase Auth provides built-in persistence modes:
- `LOCAL` - Persists across browser sessions (default)
- `SESSION` - Persists only for current session
- `NONE` - No persistence (in-memory only)

**Recommended:** Use `LOCAL` for better UX (users stay logged in)

---

## Implementation Strategy

### Phase 1: Foundation (Day 1-2)
1. Install Firebase dependencies
2. Create Firebase configuration
3. Initialize Firebase in app
4. Create authentication service
5. Create basic login component

### Phase 2: HTTP Integration (Day 3-4)
6. Create HTTP interceptor for token injection
7. Update error handling for 401/403
8. Test API integration with protected endpoints

### Phase 3: UI & UX (Day 5-6)
9. Create login page with form validation
10. Create user menu component (logout, profile)
11. Implement route guards
12. Add loading states and error messages

### Phase 4: Polish & Testing (Day 7-8)
13. Add route protection to all authenticated routes
14. Implement comprehensive error handling
15. Write unit tests
16. Write integration tests
17. Update documentation

---

## Service Layer Implementation

### 1. Firebase Configuration Service

**File:** `src/app/core/config/firebase.config.ts`

```typescript
import { InjectionToken } from '@angular/core';

export interface FirebaseConfig {
  apiKey: string;
  authDomain: string;
  projectId: string;
  storageBucket: string;
  messagingSenderId: string;
  appId: string;
}

export const FIREBASE_CONFIG = new InjectionToken<FirebaseConfig>('firebase.config');

export const firebaseConfig: FirebaseConfig = {
  apiKey: 'YOUR_API_KEY',
  authDomain: 'YOUR_PROJECT_ID.firebaseapp.com',
  projectId: 'YOUR_PROJECT_ID',
  storageBucket: 'YOUR_PROJECT_ID.appspot.com',
  messagingSenderId: 'YOUR_MESSAGING_SENDER_ID',
  appId: 'YOUR_APP_ID'
};
```

**Environment-based Configuration:**

`src/environments/environment.ts`:
```typescript
export const environment = {
  production: false,
  firebase: {
    apiKey: 'YOUR_DEV_API_KEY',
    authDomain: 'discovery-notebooks.firebaseapp.com',
    projectId: 'discovery-notebooks',
    storageBucket: 'discovery-notebooks.appspot.com',
    messagingSenderId: '123456789',
    appId: '1:123456789:web:abc123'
  },
  apiBaseUrl: 'http://localhost:8000'
};
```

`src/environments/environment.prod.ts`:
```typescript
export const environment = {
  production: true,
  firebase: {
    apiKey: 'YOUR_PROD_API_KEY',
    authDomain: 'discovery-notebooks.firebaseapp.com',
    projectId: 'discovery-notebooks',
    storageBucket: 'discovery-notebooks.appspot.com',
    messagingSenderId: '123456789',
    appId: '1:123456789:web:abc123'
  },
  apiBaseUrl: 'https://api.yourdomain.com'
};
```

### 2. Authentication Service

**File:** `src/app/core/services/auth.service.ts`

```typescript
import { Injectable, inject, signal, computed } from '@angular/core';
import { Observable, BehaviorSubject, from, of, throwError } from 'rxjs';
import { map, catchError, tap, switchMap } from 'rxjs/operators';
import { 
  Auth, 
  signInWithEmailAndPassword, 
  signOut, 
  createUserWithEmailAndPassword,
  User,
  user,
  UserCredential,
  AuthError,
  updateProfile
} from '@angular/fire/auth';

export interface AuthUser {
  uid: string;
  email: string;
  displayName: string | null;
  photoURL: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignupCredentials extends LoginCredentials {
  displayName?: string;
}

export interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private auth = inject(Auth);
  
  // Signals for reactive state management
  private authState = signal<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null
  });

  // Public computed signals
  readonly user = computed(() => this.authState().user);
  readonly isAuthenticated = computed(() => this.authState().isAuthenticated);
  readonly isLoading = computed(() => this.authState().isLoading);
  readonly error = computed(() => this.authState().error);

  // Observable for compatibility with older Angular patterns
  private currentUser$ = new BehaviorSubject<AuthUser | null>(null);
  readonly currentUser = this.currentUser$.asObservable();

  constructor() {
    this.initializeAuthListener();
  }

  /**
   * Initialize Firebase auth state listener
   */
  private initializeAuthListener(): void {
    user(this.auth).subscribe({
      next: (firebaseUser: User | null) => {
        if (firebaseUser) {
          const authUser: AuthUser = {
            uid: firebaseUser.uid,
            email: firebaseUser.email!,
            displayName: firebaseUser.displayName,
            photoURL: firebaseUser.photoURL
          };
          
          this.authState.update(state => ({
            ...state,
            user: authUser,
            isAuthenticated: true,
            isLoading: false,
            error: null
          }));
          
          this.currentUser$.next(authUser);
        } else {
          this.authState.update(state => ({
            ...state,
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null
          }));
          
          this.currentUser$.next(null);
        }
      },
      error: (error: AuthError) => {
        console.error('Auth state error:', error);
        this.authState.update(state => ({
          ...state,
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: error.message
        }));
      }
    });
  }

  /**
   * Sign in with email and password
   */
  login(credentials: LoginCredentials): Observable<UserCredential> {
    this.authState.update(state => ({ ...state, isLoading: true, error: null }));
    
    return from(
      signInWithEmailAndPassword(this.auth, credentials.email, credentials.password)
    ).pipe(
      tap(() => {
        this.authState.update(state => ({ ...state, isLoading: false }));
      }),
      catchError((error: AuthError) => {
        const errorMessage = this.getErrorMessage(error);
        this.authState.update(state => ({
          ...state,
          isLoading: false,
          error: errorMessage
        }));
        return throwError(() => new Error(errorMessage));
      })
    );
  }

  /**
   * Create new user account
   */
  signup(credentials: SignupCredentials): Observable<UserCredential> {
    this.authState.update(state => ({ ...state, isLoading: true, error: null }));
    
    return from(
      createUserWithEmailAndPassword(this.auth, credentials.email, credentials.password)
    ).pipe(
      switchMap((userCredential) => {
        // Update profile with display name if provided
        if (credentials.displayName && userCredential.user) {
          return from(
            updateProfile(userCredential.user, { displayName: credentials.displayName })
          ).pipe(map(() => userCredential));
        }
        return of(userCredential);
      }),
      tap(() => {
        this.authState.update(state => ({ ...state, isLoading: false }));
      }),
      catchError((error: AuthError) => {
        const errorMessage = this.getErrorMessage(error);
        this.authState.update(state => ({
          ...state,
          isLoading: false,
          error: errorMessage
        }));
        return throwError(() => new Error(errorMessage));
      })
    );
  }

  /**
   * Sign out current user
   */
  logout(): Observable<void> {
    return from(signOut(this.auth)).pipe(
      tap(() => {
        this.authState.update(state => ({
          ...state,
          user: null,
          isAuthenticated: false,
          error: null
        }));
      }),
      catchError((error: AuthError) => {
        console.error('Logout error:', error);
        return throwError(() => error);
      })
    );
  }

  /**
   * Get current user's ID token (for API authentication)
   */
  getIdToken(): Observable<string | null> {
    const currentUser = this.auth.currentUser;
    
    if (!currentUser) {
      return of(null);
    }

    return from(currentUser.getIdToken()).pipe(
      catchError((error: AuthError) => {
        console.error('Error getting ID token:', error);
        return of(null);
      })
    );
  }

  /**
   * Force refresh the ID token
   */
  refreshToken(): Observable<string | null> {
    const currentUser = this.auth.currentUser;
    
    if (!currentUser) {
      return of(null);
    }

    return from(currentUser.getIdToken(true)).pipe(
      catchError((error: AuthError) => {
        console.error('Error refreshing token:', error);
        return of(null);
      })
    );
  }

  /**
   * Clear error state
   */
  clearError(): void {
    this.authState.update(state => ({ ...state, error: null }));
  }

  /**
   * Convert Firebase auth errors to user-friendly messages
   */
  private getErrorMessage(error: AuthError): string {
    switch (error.code) {
      case 'auth/invalid-email':
        return 'Invalid email address format.';
      case 'auth/user-disabled':
        return 'This account has been disabled.';
      case 'auth/user-not-found':
        return 'No account found with this email.';
      case 'auth/wrong-password':
        return 'Incorrect password.';
      case 'auth/email-already-in-use':
        return 'An account already exists with this email.';
      case 'auth/weak-password':
        return 'Password should be at least 6 characters.';
      case 'auth/operation-not-allowed':
        return 'Email/password accounts are not enabled.';
      case 'auth/too-many-requests':
        return 'Too many failed attempts. Please try again later.';
      case 'auth/network-request-failed':
        return 'Network error. Please check your connection.';
      default:
        return error.message || 'An authentication error occurred.';
    }
  }
}
```

### 3. User Profile Service (Optional Enhancement)

**File:** `src/app/core/services/user-profile.service.ts`

```typescript
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { AuthService } from './auth.service';

export interface UserProfile {
  email: string;
  displayName: string;
  initials: string;
  photoURL: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class UserProfileService {
  private authService = inject(AuthService);

  /**
   * Get user profile information
   */
  getUserProfile(): Observable<UserProfile | null> {
    return this.authService.currentUser.pipe(
      map(user => {
        if (!user) return null;

        const displayName = user.displayName || user.email.split('@')[0];
        const initials = this.getInitials(displayName);

        return {
          email: user.email,
          displayName,
          initials,
          photoURL: user.photoURL
        };
      })
    );
  }

  /**
   * Extract initials from display name
   */
  private getInitials(name: string): string {
    const parts = name.trim().split(' ');
    if (parts.length === 1) {
      return parts[0].substring(0, 2).toUpperCase();
    }
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
}
```

---

## HTTP Interceptor Implementation

### Authentication Interceptor

**File:** `src/app/core/interceptors/auth.interceptor.ts`

```typescript
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

/**
 * HTTP Interceptor to add Firebase ID token to all API requests
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Skip authentication for login/signup requests
  if (req.url.includes('/auth/') || req.url.includes('firebaseapp.com')) {
    return next(req);
  }

  // Get ID token and add to request
  return authService.getIdToken().pipe(
    switchMap(token => {
      // Clone request and add authorization header if token exists
      const authReq = token
        ? req.clone({
            setHeaders: {
              Authorization: `Bearer ${token}`
            }
          })
        : req;

      // Send the request
      return next(authReq).pipe(
        catchError((error: HttpErrorResponse) => {
          // Handle authentication errors
          if (error.status === 401) {
            // Token expired or invalid - logout and redirect to login
            authService.logout().subscribe(() => {
              router.navigate(['/login'], {
                queryParams: { returnUrl: router.url }
              });
            });
          }

          if (error.status === 403) {
            // Forbidden - user doesn't have permission
            console.error('Access forbidden:', error);
            // Optionally redirect to a "no permission" page
          }

          return throwError(() => error);
        })
      );
    })
  );
};
```

### Register Interceptor in App Config

**File:** `src/app/app.config.ts`

```typescript
import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideFirebaseApp, initializeApp } from '@angular/fire/app';
import { provideAuth, getAuth } from '@angular/fire/auth';

import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { environment } from '../environments/environment';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(
      withInterceptors([authInterceptor])
    ),
    provideFirebaseApp(() => initializeApp(environment.firebase)),
    provideAuth(() => getAuth())
  ]
};
```

---

## UI Components

### 1. Login Component

**File:** `src/app/auth/login/login.component.ts`

```typescript
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  loginForm: FormGroup;
  isSubmitting = signal(false);
  errorMessage = signal<string | null>(null);
  showPassword = signal(false);

  constructor() {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]]
    });
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.isSubmitting.set(true);
    this.errorMessage.set(null);

    const credentials = this.loginForm.value;

    this.authService.login(credentials).subscribe({
      next: () => {
        // Get return URL from query params or default to notebooks
        const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/notebooks';
        this.router.navigate([returnUrl]);
      },
      error: (error) => {
        this.errorMessage.set(error.message);
        this.isSubmitting.set(false);
      }
    });
  }

  togglePasswordVisibility(): void {
    this.showPassword.update(value => !value);
  }

  get email() {
    return this.loginForm.get('email');
  }

  get password() {
    return this.loginForm.get('password');
  }
}
```

**File:** `src/app/auth/login/login.component.html`

```html
<div class="login-container">
  <div class="login-card">
    <div class="login-header">
      <h1>Welcome to Discovery</h1>
      <p>Sign in to your account</p>
    </div>

    <form [formGroup]="loginForm" (ngSubmit)="onSubmit()" class="login-form">
      <!-- Error Message -->
      @if (errorMessage()) {
        <div class="alert alert-error">
          {{ errorMessage() }}
        </div>
      }

      <!-- Email Field -->
      <div class="form-group">
        <label for="email">Email</label>
        <input
          id="email"
          type="email"
          formControlName="email"
          placeholder="you@example.com"
          [class.error]="email?.invalid && email?.touched"
        />
        @if (email?.invalid && email?.touched) {
          <div class="error-message">
            @if (email?.errors?.['required']) {
              <span>Email is required</span>
            }
            @if (email?.errors?.['email']) {
              <span>Please enter a valid email</span>
            }
          </div>
        }
      </div>

      <!-- Password Field -->
      <div class="form-group">
        <label for="password">Password</label>
        <div class="password-input-wrapper">
          <input
            id="password"
            [type]="showPassword() ? 'text' : 'password'"
            formControlName="password"
            placeholder="Enter your password"
            [class.error]="password?.invalid && password?.touched"
          />
          <button
            type="button"
            class="password-toggle"
            (click)="togglePasswordVisibility()"
          >
            {{ showPassword() ? '👁️' : '👁️‍🗨️' }}
          </button>
        </div>
        @if (password?.invalid && password?.touched) {
          <div class="error-message">
            @if (password?.errors?.['required']) {
              <span>Password is required</span>
            }
            @if (password?.errors?.['minlength']) {
              <span>Password must be at least 6 characters</span>
            }
          </div>
        }
      </div>

      <!-- Submit Button -->
      <button
        type="submit"
        class="btn btn-primary btn-block"
        [disabled]="isSubmitting()"
      >
        @if (isSubmitting()) {
          <span>Signing in...</span>
        } @else {
          <span>Sign In</span>
        }
      </button>

      <!-- Sign Up Link -->
      <div class="form-footer">
        <p>
          Don't have an account?
          <a routerLink="/signup">Sign up</a>
        </p>
      </div>
    </form>
  </div>
</div>
```

### 2. User Menu Component

**File:** `src/app/shared/user-menu/user-menu.component.ts`

```typescript
import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { UserProfileService } from '../../core/services/user-profile.service';

@Component({
  selector: 'app-user-menu',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './user-menu.component.html',
  styleUrls: ['./user-menu.component.scss']
})
export class UserMenuComponent {
  private authService = inject(AuthService);
  private userProfileService = inject(UserProfileService);
  private router = inject(Router);

  userProfile$ = this.userProfileService.getUserProfile();
  isMenuOpen = signal(false);

  toggleMenu(): void {
    this.isMenuOpen.update(value => !value);
  }

  closeMenu(): void {
    this.isMenuOpen.set(false);
  }

  logout(): void {
    this.authService.logout().subscribe({
      next: () => {
        this.router.navigate(['/login']);
      },
      error: (error) => {
        console.error('Logout failed:', error);
      }
    });
  }
}
```

**File:** `src/app/shared/user-menu/user-menu.component.html`

```html
<div class="user-menu">
  @if (userProfile$ | async; as profile) {
    <button class="user-menu-trigger" (click)="toggleMenu()">
      @if (profile.photoURL) {
        <img [src]="profile.photoURL" [alt]="profile.displayName" class="user-avatar" />
      } @else {
        <div class="user-avatar-placeholder">
          {{ profile.initials }}
        </div>
      }
      <span class="user-name">{{ profile.displayName }}</span>
      <svg class="dropdown-icon" width="16" height="16" viewBox="0 0 16 16">
        <path d="M4 6l4 4 4-4" stroke="currentColor" fill="none" stroke-width="2"/>
      </svg>
    </button>

    @if (isMenuOpen()) {
      <div class="user-menu-dropdown" (click)="closeMenu()">
        <div class="user-menu-header">
          <div class="user-email">{{ profile.email }}</div>
        </div>
        <div class="user-menu-divider"></div>
        <button class="user-menu-item" (click)="logout()">
          <svg width="16" height="16" viewBox="0 0 16 16" class="menu-icon">
            <path d="M6 14H2V2h4M11 11l3-3-3-3M4 8h10" stroke="currentColor" fill="none" stroke-width="2"/>
          </svg>
          Sign Out
        </button>
      </div>
    }
  }
</div>
```

### 3. Signup Component (Optional)

**File:** `src/app/auth/signup/signup.component.ts`

```typescript
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './signup.component.html',
  styleUrls: ['./signup.component.scss']
})
export class SignupComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);

  signupForm: FormGroup;
  isSubmitting = signal(false);
  errorMessage = signal<string | null>(null);

  constructor() {
    this.signupForm = this.fb.group({
      displayName: ['', [Validators.required]],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      confirmPassword: ['', [Validators.required]]
    }, {
      validators: this.passwordMatchValidator
    });
  }

  passwordMatchValidator(g: FormGroup) {
    return g.get('password')?.value === g.get('confirmPassword')?.value
      ? null : { mismatch: true };
  }

  onSubmit(): void {
    if (this.signupForm.invalid) {
      this.signupForm.markAllAsTouched();
      return;
    }

    this.isSubmitting.set(true);
    this.errorMessage.set(null);

    const { displayName, email, password } = this.signupForm.value;

    this.authService.signup({ email, password, displayName }).subscribe({
      next: () => {
        this.router.navigate(['/notebooks']);
      },
      error: (error) => {
        this.errorMessage.set(error.message);
        this.isSubmitting.set(false);
      }
    });
  }
}
```

---

## Route Guards

### Authentication Guard

**File:** `src/app/core/guards/auth.guard.ts`

```typescript
import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { map, take } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';

/**
 * Route guard to protect routes that require authentication
 */
export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return authService.currentUser.pipe(
    take(1),
    map(user => {
      if (user) {
        return true;
      }

      // Redirect to login with return URL
      return router.createUrlTree(['/login'], {
        queryParams: { returnUrl: state.url }
      });
    })
  );
};

/**
 * Route guard to redirect authenticated users away from login/signup
 */
export const noAuthGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return authService.currentUser.pipe(
    take(1),
    map(user => {
      if (!user) {
        return true;
      }

      // Already authenticated, redirect to notebooks
      return router.createUrlTree(['/notebooks']);
    })
  );
};
```

### Update Routes

**File:** `src/app/app.routes.ts`

```typescript
import { Routes } from '@angular/router';
import { authGuard, noAuthGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  // Public routes
  {
    path: 'login',
    loadComponent: () => import('./auth/login/login.component').then(m => m.LoginComponent),
    canActivate: [noAuthGuard]
  },
  {
    path: 'signup',
    loadComponent: () => import('./auth/signup/signup.component').then(m => m.SignupComponent),
    canActivate: [noAuthGuard]
  },

  // Protected routes
  {
    path: 'notebooks',
    loadComponent: () => import('./notebook-list/notebook-list.component').then(m => m.NotebookListComponent),
    canActivate: [authGuard]
  },
  {
    path: 'notebooks/:id',
    loadComponent: () => import('./notebook-detail/notebook-detail.component').then(m => m.NotebookDetailComponent),
    canActivate: [authGuard]
  },
  {
    path: 'notebooks/:id/chat',
    loadComponent: () => import('./chat/chat.component').then(m => m.ChatComponent),
    canActivate: [authGuard]
  },

  // Default redirect
  {
    path: '',
    redirectTo: 'notebooks',
    pathMatch: 'full'
  },

  // Catch-all redirect
  {
    path: '**',
    redirectTo: 'notebooks'
  }
];
```

---

## State Management

### Authentication State Pattern

The app uses **Angular Signals** for reactive state management:

**Benefits:**
- ✅ Built-in to Angular 21 (no additional libraries)
- ✅ Fine-grained reactivity
- ✅ Better performance than Observables for state
- ✅ Simpler mental model

**State Flow:**

```
Firebase Auth State Change
         ↓
   Auth Service (Signals)
         ↓
   Components (computed/effect)
         ↓
   Template (automatic updates)
```

**Usage in Components:**

```typescript
import { Component, inject, computed } from '@angular/core';
import { AuthService } from './core/services/auth.service';

@Component({...})
export class AppComponent {
  private authService = inject(AuthService);

  // Direct access to signals
  user = this.authService.user;
  isAuthenticated = this.authService.isAuthenticated;

  // Computed values
  userDisplayName = computed(() => {
    const user = this.user();
    return user?.displayName || user?.email || 'Anonymous';
  });
}
```

**Template Usage:**

```html
@if (isAuthenticated()) {
  <app-user-menu></app-user-menu>
} @else {
  <a routerLink="/login">Sign In</a>
}
```

---

## Error Handling

### Global Error Handling Strategy

**1. Authentication Errors**
- Handled in `AuthService`
- User-friendly error messages
- Automatic logout on 401

**2. HTTP Errors**
- Interceptor catches 401/403
- Automatic redirect to login
- Preserve return URL

**3. Network Errors**
- Display connection error message
- Retry mechanism for failed requests
- Offline mode detection

**Error Display Component:**

**File:** `src/app/shared/error-alert/error-alert.component.ts`

```typescript
import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-error-alert',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (message) {
      <div class="alert alert-error">
        <svg class="alert-icon" width="20" height="20" viewBox="0 0 20 20">
          <path d="M10 0C4.48 0 0 4.48 0 10s4.48 10 10 10 10-4.48 10-10S15.52 0 10 0zm1 15H9v-2h2v2zm0-4H9V5h2v6z" fill="currentColor"/>
        </svg>
        <span class="alert-message">{{ message }}</span>
        @if (dismissible) {
          <button class="alert-close" (click)="dismiss.emit()">
            <svg width="16" height="16" viewBox="0 0 16 16">
              <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="2"/>
            </svg>
          </button>
        }
      </div>
    }
  `,
  styles: [`
    .alert-error {
      display: flex;
      align-items: center;
      padding: 12px 16px;
      background-color: #fee;
      border: 1px solid #fcc;
      border-radius: 6px;
      color: #c33;
      margin-bottom: 16px;
    }
    .alert-icon {
      margin-right: 12px;
      flex-shrink: 0;
    }
    .alert-message {
      flex: 1;
    }
    .alert-close {
      background: none;
      border: none;
      cursor: pointer;
      padding: 4px;
      margin-left: 12px;
    }
  `]
})
export class ErrorAlertComponent {
  @Input() message: string | null = null;
  @Input() dismissible: boolean = true;
  @Output() dismiss = new EventEmitter<void>();
}
```

---

## Testing Requirements

### Unit Tests

**Test Authentication Service:**

**File:** `src/app/core/services/auth.service.spec.ts`

```typescript
import { TestBed } from '@angular/core/testing';
import { AuthService } from './auth.service';
import { Auth } from '@angular/fire/auth';

describe('AuthService', () => {
  let service: AuthService;
  let mockAuth: jasmine.SpyObj<Auth>;

  beforeEach(() => {
    mockAuth = jasmine.createSpyObj('Auth', ['signInWithEmailAndPassword', 'signOut']);

    TestBed.configureTestingModule({
      providers: [
        AuthService,
        { provide: Auth, useValue: mockAuth }
      ]
    });

    service = TestBed.inject(AuthService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should login with valid credentials', (done) => {
    const mockCredential = { user: { email: 'test@test.com' } };
    mockAuth.signInWithEmailAndPassword.and.returnValue(Promise.resolve(mockCredential as any));

    service.login({ email: 'test@test.com', password: 'password' }).subscribe({
      next: (result) => {
        expect(result).toBeTruthy();
        done();
      }
    });
  });

  it('should handle login errors', (done) => {
    mockAuth.signInWithEmailAndPassword.and.returnValue(
      Promise.reject({ code: 'auth/wrong-password', message: 'Wrong password' })
    );

    service.login({ email: 'test@test.com', password: 'wrong' }).subscribe({
      error: (error) => {
        expect(error.message).toBe('Incorrect password.');
        done();
      }
    });
  });

  it('should logout successfully', (done) => {
    mockAuth.signOut.and.returnValue(Promise.resolve());

    service.logout().subscribe({
      next: () => {
        expect(mockAuth.signOut).toHaveBeenCalled();
        done();
      }
    });
  });
});
```

**Test Route Guards:**

```typescript
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { authGuard } from './auth.guard';
import { AuthService } from '../services/auth.service';
import { of } from 'rxjs';

describe('authGuard', () => {
  let authService: jasmine.SpyObj<AuthService>;
  let router: jasmine.SpyObj<Router>;

  beforeEach(() => {
    authService = jasmine.createSpyObj('AuthService', [], {
      currentUser: of({ email: 'test@test.com', uid: '123' })
    });
    router = jasmine.createSpyObj('Router', ['createUrlTree']);

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: authService },
        { provide: Router, useValue: router }
      ]
    });
  });

  it('should allow access for authenticated users', (done) => {
    const result = authGuard({} as any, {} as any);
    if (result instanceof Observable) {
      result.subscribe(canActivate => {
        expect(canActivate).toBe(true);
        done();
      });
    }
  });
});
```

### Integration Tests

**Test Login Flow:**

```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { LoginComponent } from './login.component';
import { AuthService } from '../../core/services/auth.service';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';

describe('LoginComponent Integration', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let authService: jasmine.SpyObj<AuthService>;
  let router: jasmine.SpyObj<Router>;

  beforeEach(async () => {
    authService = jasmine.createSpyObj('AuthService', ['login']);
    router = jasmine.createSpyObj('Router', ['navigate']);

    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [
        { provide: AuthService, useValue: authService },
        { provide: Router, useValue: router }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should validate email format', () => {
    component.loginForm.patchValue({
      email: 'invalid-email',
      password: 'password123'
    });

    component.onSubmit();

    expect(authService.login).not.toHaveBeenCalled();
    expect(component.loginForm.get('email')?.hasError('email')).toBe(true);
  });

  it('should call authService.login on valid form submission', () => {
    authService.login.and.returnValue(of({} as any));

    component.loginForm.patchValue({
      email: 'test@test.com',
      password: 'password123'
    });

    component.onSubmit();

    expect(authService.login).toHaveBeenCalledWith({
      email: 'test@test.com',
      password: 'password123'
    });
  });

  it('should navigate to notebooks on successful login', () => {
    authService.login.and.returnValue(of({} as any));

    component.loginForm.patchValue({
      email: 'test@test.com',
      password: 'password123'
    });

    component.onSubmit();

    expect(router.navigate).toHaveBeenCalledWith(['/notebooks']);
  });

  it('should display error message on login failure', () => {
    authService.login.and.returnValue(
      throwError(() => new Error('Invalid credentials'))
    );

    component.loginForm.patchValue({
      email: 'test@test.com',
      password: 'wrong'
    });

    component.onSubmit();

    expect(component.errorMessage()).toBe('Invalid credentials');
    expect(component.isSubmitting()).toBe(false);
  });
});
```

### E2E Tests

**Test Complete Authentication Flow:**

```typescript
import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should login and access protected route', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');

    // Fill in credentials
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');

    // Click login button
    await page.click('button[type="submit"]');

    // Wait for navigation to notebooks
    await page.waitForURL('/notebooks');

    // Verify we're on the notebooks page
    expect(page.url()).toContain('/notebooks');

    // Verify user menu is visible
    await expect(page.locator('.user-menu')).toBeVisible();
  });

  test('should redirect to login when accessing protected route', async ({ page }) => {
    // Try to access protected route without authentication
    await page.goto('/notebooks');

    // Should be redirected to login
    await page.waitForURL(/\/login/);
    expect(page.url()).toContain('/login');
    expect(page.url()).toContain('returnUrl');
  });

  test('should logout successfully', async ({ page, context }) => {
    // Login first
    await page.goto('/login');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/notebooks');

    // Open user menu
    await page.click('.user-menu-trigger');

    // Click logout
    await page.click('text=Sign Out');

    // Should redirect to login
    await page.waitForURL('/login');
    expect(page.url()).toContain('/login');
  });
});
```

---

## Implementation Checklist

### Dependencies
- [ ] Install `@angular/fire` or Firebase SDK
- [ ] Install Playwright for E2E testing (optional)
- [ ] Update `package.json` with new dependencies

### Firebase Setup
- [ ] Create Firebase project in console
- [ ] Enable Email/Password authentication
- [ ] Generate Firebase config (API keys, project ID, etc.)
- [ ] Add Firebase config to environment files
- [ ] Test Firebase connection

### Core Services
- [ ] Create `AuthService` with login/logout/signup
- [ ] Create `UserProfileService` (optional)
- [ ] Implement token retrieval methods
- [ ] Add error handling and user-friendly messages
- [ ] Write unit tests for services

### HTTP Layer
- [ ] Create `authInterceptor` for token injection
- [ ] Register interceptor in app config
- [ ] Handle 401/403 errors in interceptor
- [ ] Test interceptor with mock requests

### Route Protection
- [ ] Create `authGuard` for protected routes
- [ ] Create `noAuthGuard` for public routes
- [ ] Apply guards to all routes in `app.routes.ts`
- [ ] Test route protection

### UI Components
- [ ] Create LoginComponent with form validation
- [ ] Create SignupComponent (optional)
- [ ] Create UserMenuComponent with logout
- [ ] Create ErrorAlertComponent
- [ ] Add loading states and spinners
- [ ] Style components for light/dark mode

### Integration
- [ ] Update `app.config.ts` with Firebase providers
- [ ] Update main layout to show user menu when authenticated
- [ ] Add conditional rendering based on auth state
- [ ] Test complete login → API call → logout flow

### Testing
- [ ] Unit tests for AuthService (login, logout, token)
- [ ] Unit tests for auth guards
- [ ] Component tests for LoginComponent
- [ ] Component tests for UserMenuComponent
- [ ] Integration tests for HTTP interceptor
- [ ] E2E tests for authentication flow

### Documentation
- [ ] Update README with Firebase setup instructions
- [ ] Document environment variables
- [ ] Create Firebase configuration guide
- [ ] Add troubleshooting section
- [ ] Update API integration docs

### Deployment
- [ ] Test in development environment
- [ ] Configure Firebase for production
- [ ] Set up environment variables in hosting
- [ ] Test production build
- [ ] Monitor authentication metrics

---

## Security Considerations

### Token Security
- ✅ Tokens managed by Firebase (secure by default)
- ✅ Automatic token refresh (Firebase handles this)
- ✅ Tokens stored in memory, not localStorage (XSS protection)
- ✅ HTTPS enforced in production

### CORS Configuration
- Update backend CORS to allow only production domain
- Configure Firebase Auth authorized domains

### Password Security
- Firebase enforces minimum 6-character passwords
- Consider adding password strength meter
- Implement password reset flow (Firebase provides this)

### Session Security
- Use Firebase's built-in session persistence
- Consider implementing "Remember Me" option
- Auto-logout after inactivity (optional)

---

## Future Enhancements

### Social Authentication
- Google Sign-In
- GitHub Sign-In
- Microsoft Sign-In

### Advanced Features
- Email verification
- Password reset
- Multi-factor authentication (MFA)
- Account deletion
- Profile management

### User Experience
- Remember last used email
- Biometric authentication (WebAuthn)
- Session timeout warnings
- Concurrent session management

---

## Backend Alignment

This frontend implementation aligns with the backend specification (`prompts/firebase_login_backend_spec.md`) through:

1. **Token Exchange:**
   - Frontend retrieves Firebase ID token
   - Token sent in `Authorization: Bearer <token>` header
   - Backend verifies token and extracts user email

2. **User Identification:**
   - Frontend gets user email from Firebase Auth
   - Backend uses email as `created_by` field
   - Both systems use email as primary identifier

3. **Authorization:**
   - Backend filters resources by `created_by` email
   - Frontend only sees own resources in API responses
   - 404 responses hide existence of other users' resources

4. **Error Handling:**
   - Frontend interceptor catches 401 → logout
   - Frontend interceptor catches 403 → access denied
   - Backend returns appropriate HTTP status codes

5. **Security Model:**
   - Frontend: Firebase handles authentication
   - Backend: Firebase Admin SDK validates tokens
   - Both: User email is source of truth for ownership

---

## References

- [AngularFire Documentation](https://github.com/angular/angularfire)
- [Firebase Auth Web Guide](https://firebase.google.com/docs/auth/web/start)
- [Angular HttpClient](https://angular.dev/guide/http)
- [Angular Router Guards](https://angular.dev/guide/routing/common-router-tasks#preventing-unauthorized-access)
- [Angular Signals](https://angular.dev/guide/signals)
- [Backend Specification](./firebase_login_backend_spec.md)

---

**End of Frontend Specification**
