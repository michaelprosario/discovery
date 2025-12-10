# Firebase Authentication Setup Guide

This guide will help you configure Firebase Authentication for the Discovery Portal frontend application.

## Overview

The application now has Firebase Authentication integrated with:
- ✅ Login component with email/password authentication
- ✅ HTTP interceptor that automatically adds Firebase ID tokens to API requests
- ✅ Route guards protecting all authenticated routes
- ✅ User menu component with logout functionality
- ✅ Reactive state management using Angular Signals

## Prerequisites

- Firebase project created (if not, create one at https://console.firebase.google.com)
- Firebase Authentication enabled with Email/Password provider
- Firebase config details from your project

## Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Click "Add project" or select existing project
3. Follow the setup wizard
4. Once created, click on the "Web" icon (</>) to add a web app
5. Register your app with a nickname (e.g., "Discovery Portal")
6. Copy the Firebase configuration object

## Step 2: Enable Email/Password Authentication

1. In Firebase Console, go to **Authentication** > **Sign-in method**
2. Click on **Email/Password**
3. Enable **Email/Password** (first toggle)
4. Optionally enable **Email link (passwordless sign-in)**
5. Click **Save**

## Step 3: Configure Environment Files

Update the Firebase configuration in your environment files with the values from your Firebase project.

### Development Environment

Edit `discoveryPortal/src/environments/environment.development.ts`:

```typescript
export const environment = {
  production: false,
  apiUrl: '/api',
  firebase: {
    apiKey: 'YOUR_DEV_API_KEY',
    authDomain: 'YOUR_PROJECT_ID.firebaseapp.com',
    projectId: 'YOUR_PROJECT_ID',
    storageBucket: 'YOUR_PROJECT_ID.appspot.com',
    messagingSenderId: 'YOUR_MESSAGING_SENDER_ID',
    appId: 'YOUR_APP_ID'
  }
};
```

### Production Environment

Edit `discoveryPortal/src/environments/environment.production.ts`:

```typescript
export const environment = {
  production: true,
  apiUrl: '/',  // For Firebase Hosting with Cloud Run backend
  firebase: {
    apiKey: 'YOUR_PROD_API_KEY',
    authDomain: 'YOUR_PROJECT_ID.firebaseapp.com',
    projectId: 'YOUR_PROJECT_ID',
    storageBucket: 'YOUR_PROJECT_ID.appspot.com',
    messagingSenderId: 'YOUR_MESSAGING_SENDER_ID',
    appId: 'YOUR_APP_ID'
  }
};
```

**Where to find these values:**
- Go to Firebase Console > Project Settings > General
- Scroll down to "Your apps" section
- Click on your web app
- Copy the config object values

## Step 4: Create Test User

To test the authentication:

1. Go to Firebase Console > Authentication > Users
2. Click "Add user"
3. Enter email and password
4. Click "Add user"

OR use the signup functionality (if you create a signup component - optional).

## Step 5: Configure Authorized Domains

For production deployment:

1. Go to Firebase Console > Authentication > Settings > Authorized domains
2. Add your production domain (e.g., `your-app.web.app` or custom domain)
3. For local development, `localhost` is already authorized by default

## Step 6: Test the Application

1. Start the development server:
   ```bash
   cd discoveryPortal
   npm start
   ```

2. Navigate to `http://localhost:4200`
3. You should be redirected to `/login`
4. Enter the test user credentials
5. Upon successful login, you should be redirected to the notebook list
6. You should see the user menu in the side navigation

## Architecture

### Authentication Flow

```
User enters credentials
        ↓
LoginComponent calls AuthService.login()
        ↓
Firebase Auth validates credentials
        ↓
AuthService updates user state (signals)
        ↓
User redirected to protected route
        ↓
AuthGuard allows access
        ↓
User makes API request
        ↓
AuthInterceptor adds Bearer token
        ↓
Backend validates token
        ↓
API returns user's data
```

### Key Components

1. **AuthService** (`src/app/core/services/auth.service.ts`)
   - Manages Firebase authentication state
   - Provides login, logout, signup methods
   - Exposes user state via signals
   - Retrieves ID tokens for API calls

2. **AuthInterceptor** (`src/app/core/interceptors/auth.interceptor.ts`)
   - Automatically adds Firebase ID token to HTTP requests
   - Handles 401 errors by logging out user
   - Skips authentication for Firebase URLs

3. **AuthGuard** (`src/app/core/guards/auth.guard.ts`)
   - Protects routes from unauthenticated access
   - Redirects to login with return URL
   - `noAuthGuard` prevents authenticated users from accessing login

4. **LoginComponent** (`src/app/auth/login/login.component.ts`)
   - Email/password login form
   - Form validation
   - Error handling
   - Loading states

5. **UserMenuComponent** (`src/app/shared/user-menu/user-menu.component.ts`)
   - Displays user info
   - Logout functionality
   - Avatar with initials

## Deployment

### Firebase Hosting Setup

1. Install Firebase CLI:
   ```bash
   npm install -g firebase-tools
   ```

2. Login to Firebase:
   ```bash
   firebase login
   ```

3. Initialize Firebase Hosting:
   ```bash
   cd discoveryPortal
   firebase init hosting
   ```

4. Configure `firebase.json`:
   ```json
   {
     "hosting": {
       "public": "dist/discovery-portal/browser",
       "ignore": [
         "firebase.json",
         "**/.*",
         "**/node_modules/**"
       ],
       "rewrites": [
         {
           "source": "/api/**",
           "run": {
             "serviceId": "YOUR_CLOUD_RUN_SERVICE",
             "region": "us-central1"
           }
         },
         {
           "source": "**",
           "destination": "/index.html"
         }
       ]
     }
   }
   ```

5. Build the app:
   ```bash
   npm run build
   ```

6. Deploy:
   ```bash
   firebase deploy --only hosting
   ```

### Google Cloud Run Backend

Your backend should be deployed to Cloud Run. The frontend will make API calls to `/api/*` which Firebase Hosting will proxy to Cloud Run.

1. Deploy backend to Cloud Run
2. Note the Cloud Run service URL
3. Configure Firebase Hosting rewrites (see above)
4. Ensure Cloud Run service has proper CORS configuration
5. Backend should validate Firebase ID tokens (see `prompts/firebase_login_backend_spec.md`)

## Environment Variables

For security, you can use environment variables for Firebase config:

1. Create `.env` file (add to `.gitignore`):
   ```
   FIREBASE_API_KEY=your_api_key
   FIREBASE_AUTH_DOMAIN=your_auth_domain
   FIREBASE_PROJECT_ID=your_project_id
   ```

2. Use environment variable replacement in build process

## Security Considerations

### Token Security
- ✅ Tokens managed by Firebase (secure by default)
- ✅ Automatic token refresh
- ✅ Tokens stored in memory, not localStorage
- ✅ HTTPS enforced in production

### Backend Validation
- Backend MUST validate Firebase ID tokens
- Use Firebase Admin SDK for validation
- Extract user email from token
- Use email for data filtering (created_by field)

### CORS Configuration
- Update backend CORS to allow only your domain
- Configure Firebase Auth authorized domains

## Troubleshooting

### "No Firebase App has been created"
- Check that Firebase is initialized in `app.module.ts`
- Verify environment configuration is correct

### "Firebase: Error (auth/invalid-api-key)"
- Double-check your API key in environment files
- Ensure you're using the correct environment

### "401 Unauthorized" on API calls
- Check that backend is validating tokens correctly
- Verify token is being sent in Authorization header
- Check backend logs for validation errors

### Login redirects to login page
- Check browser console for errors
- Verify Firebase Auth is enabled
- Check that user exists in Firebase

### CORS errors
- Verify backend CORS configuration
- Check that apiUrl in environment is correct
- For development, ensure proxy is configured

## Next Steps

### Optional Enhancements

1. **Signup Component**
   - Create user registration form
   - Email verification
   - Password strength validation

2. **Password Reset**
   - Forgot password functionality
   - Email-based password reset

3. **Social Authentication**
   - Google Sign-In
   - GitHub Sign-In

4. **Profile Management**
   - Update display name
   - Change password
   - Delete account

5. **Session Management**
   - Auto-logout on inactivity
   - Remember me functionality
   - Multi-device session tracking

## Support

For more information:
- [Firebase Authentication Docs](https://firebase.google.com/docs/auth)
- [AngularFire Documentation](https://github.com/angular/angularfire)
- Backend specification: `prompts/firebase_login_backend_spec.md`
- Frontend specification: `prompts/firebase_login_frontend_spec.md`

## Summary

The Firebase Authentication implementation is complete with:
- ✅ Firebase SDK installed and configured
- ✅ Authentication service with state management
- ✅ HTTP interceptor for automatic token injection
- ✅ Route guards for access control
- ✅ Login component with form validation
- ✅ User menu with logout
- ✅ Environment configuration setup
- ✅ Ready for Firebase Hosting deployment
- ✅ Backend integration via Cloud Run

You just need to:
1. Add your Firebase configuration to environment files
2. Create a test user in Firebase Console
3. Test the login flow
4. Deploy to Firebase Hosting (optional)
