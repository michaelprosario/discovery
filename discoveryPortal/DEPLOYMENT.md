# Firebase Hosting Deployment Guide

This guide provides step-by-step instructions for deploying the Discovery Portal Angular application to Google Firebase Hosting.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Firebase Setup](#firebase-setup)
4. [Building the Application](#building-the-application)
5. [Deployment Process](#deployment-process)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have the following:

- **Node.js** (v18 or higher) and **npm** installed
- **Angular CLI** installed globally: `npm install -g @angular/cli`
- **Firebase CLI** installed globally: `npm install -g firebase-tools`
- **Firebase Project** created at [Firebase Console](https://console.firebase.google.com)
- **Firebase Authentication** enabled with Email/Password provider
- **Git** for version control (recommended)

---

## Environment Configuration

### Critical Environment Files

The application uses Angular's environment configuration system with file replacement during build. Three critical files require proper configuration:

#### 1. `src/environments/environment.ts` (Default/Fallback)

This is the default configuration file. It's replaced during build based on the target environment.

```typescript
export const environment = {
  production: false,
  apiUrl: '/api',
  firebase: {
    apiKey: 'YOUR_API_KEY',
    authDomain: 'YOUR_PROJECT_ID.firebaseapp.com',
    projectId: 'YOUR_PROJECT_ID',
    storageBucket: 'YOUR_PROJECT_ID.appspot.com',
    messagingSenderId: 'YOUR_MESSAGING_SENDER_ID',
    appId: 'YOUR_APP_ID'
  }
};
```

#### 2. `src/environments/environment.development.ts` (Local Development)

Used during local development with `ng serve`:

```typescript
export const environment = {
  production: false,
  apiUrl: '/api',  // Uses proxy.conf.json to avoid CORS
  firebase: {
    apiKey: "YOUR_DEV_API_KEY",
    authDomain: "your-project-id.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project-id.firebasestorage.app",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_DEV_APP_ID"
  }
};
```

**Important:** This file should match your development Firebase project configuration.

#### 3. `src/environments/environment.production.ts` (Production Deployment)

**⚠️ CRITICAL:** This file is used for production builds and Firebase deployments:

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

### Getting Firebase Configuration Values

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project
3. Click the gear icon (⚙️) → **Project settings**
4. Scroll down to **Your apps** section
5. Select your web app or create one if it doesn't exist
6. Copy the configuration values from the `firebaseConfig` object

**Example of what you'll see:**
```javascript
const firebaseConfig = {
  apiKey: "AIzaSyABC123...",
  authDomain: "my-project.firebaseapp.com",
  projectId: "my-project",
  storageBucket: "my-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123..."
};
```

### Environment File Security

**⚠️ Security Best Practices:**

- **Never commit production credentials** to public repositories
- Add `environment.production.ts` to `.gitignore` if it contains sensitive data
- Use environment variables or secret management for CI/CD pipelines
- Keep development and production Firebase projects separate
- Regularly rotate API keys and credentials

---

## Firebase Setup
### 0. Install firebase tools

```
npm install -g firebase-tools
```



### 1. Initialize Firebase in Your Project

If you haven't already initialized Firebase:

```bash
cd discoveryPortal
firebase login
firebase init
```

Login to firebase.  For github codespace, you will probably need to do something like this:

```
firebase login --no-localhost
```

During initialization:
- Select **Hosting** (use spacebar to select)
- Choose your Firebase project or create a new one
- Set public directory to: `dist/discovery-portal/browser`
- Configure as single-page app: **Yes**
- Set up automatic builds with GitHub: **No** (or Yes if desired)
- Don't overwrite `firebase.json` if it already exists

### 2. Verify `firebase.json` Configuration

Ensure your `firebase.json` is properly configured:

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
          "serviceId": "discovery-api",
          "region": "us-central1"
        }
      },
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000"
          }
        ]
      },
      {
        "source": "**/*.@(jpg|jpeg|gif|png|svg|webp)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000"
          }
        ]
      }
    ]
  }
}
```

**Key Configuration Points:**
- `public`: Points to the Angular build output directory
- `rewrites`: 
  - `/api/**` routes to Cloud Run backend (if applicable)
  - All other routes serve `index.html` for Angular routing
- `headers`: Optimizes caching for static assets

---

## Building the Application

### 1. Install Dependencies

```bash
cd discoveryPortal
npm install
```

### 2. Build for Production

The production build uses the `environment.production.ts` file:

```bash
ng build --configuration production
```

Or simply:

```bash
npm run build
```

**What happens during build:**
- `environment.ts` is replaced with `environment.production.ts`
- Code is optimized and minified
- Output is generated in `dist/discovery-portal/browser/`
- Assets are hashed for cache busting

### 3. Verify Build Output

Check that the build completed successfully:

```bash
ls -la dist/discovery-portal/browser/
```

You should see:
- `index.html`
- JavaScript bundles (e.g., `main-ABC123.js`)
- CSS files
- `assets/` directory (if applicable)

---

## Deployment Process

### Option 1: Standard Deployment

Deploy to Firebase Hosting:

```bash
firebase deploy --only hosting
```

### Option 2: Deploy with Specific Project

If you have multiple Firebase projects:

```bash
firebase use production  # Switch to production project
firebase deploy --only hosting
```

Or deploy to a specific project directly:

```bash
firebase deploy --only hosting --project your-project-id
```

### Option 3: Preview Before Deployment

Create a preview channel to test before deploying to production:

```bash
firebase hosting:channel:deploy preview
```

This creates a temporary URL for testing.

### Deployment Output

Successful deployment will show:

```
✔  Deploy complete!

Project Console: https://console.firebase.google.com/project/your-project-id/overview
Hosting URL: https://your-project-id.web.app
```

---

## Post-Deployment Verification

### 1. Access the Application

Navigate to your Firebase Hosting URL:
```
https://your-project-id.web.app
```
or
```
https://your-project-id.firebaseapp.com
```

### 2. Verify Firebase Authentication

1. Navigate to the login page
2. Attempt to log in with test credentials
3. Check browser console for any errors
4. Verify that the Firebase SDK initializes correctly

### 3. Check API Connectivity

If your application connects to a backend API:

1. Open browser Developer Tools (F12)
2. Go to the **Network** tab
3. Perform actions that call the API
4. Verify that `/api/**` requests are properly routed
5. Check for CORS errors or authentication issues

### 4. Test Critical Functionality

- Navigation between routes
- Authentication flows (login, logout, protected routes)
- Data fetching and display
- Form submissions
- Error handling

---

## Troubleshooting

### Issue: Firebase Configuration Not Found

**Error:** `Firebase: Error (auth/invalid-api-key)`

**Solution:**
1. Verify `environment.production.ts` has correct Firebase config
2. Rebuild the application: `ng build --configuration production`
3. Redeploy: `firebase deploy --only hosting`

### Issue: 404 on Page Refresh

**Problem:** Refreshing on routes like `/documents` returns 404

**Solution:** Ensure `firebase.json` has the rewrite rule:
```json
{
  "source": "**",
  "destination": "/index.html"
}
```

### Issue: API Requests Failing

**Error:** API calls to `/api/**` return 404 or CORS errors

**Solution:**
1. Verify the backend Cloud Run service is deployed
2. Check `firebase.json` has the correct `serviceId` in rewrites
3. Ensure Cloud Run service allows unauthenticated requests (if applicable)

### Issue: Old Version Still Showing

**Problem:** Deployment succeeded but old version still loads

**Solution:**
1. Clear browser cache (Ctrl+Shift+Delete)
2. Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
3. Check Firebase Console → Hosting to verify deployment time
4. Verify `outputHashing: "all"` is set in `angular.json` production config

### Issue: Build Fails with Environment Errors

**Error:** Cannot find module './environments/environment'

**Solution:**
1. Ensure all three environment files exist
2. Verify `angular.json` has correct `fileReplacements` configuration
3. Check that environment files export `environment` constant

### Issue: Firebase CLI Not Authenticated

**Error:** `Error: Failed to authenticate`

**Solution:**
```bash
firebase logout
firebase login
```

---

## Continuous Deployment (Optional)

### GitHub Actions

Create `.github/workflows/firebase-hosting.yml`:

```yaml
name: Deploy to Firebase Hosting

on:
  push:
    branches:
      - main

jobs:
  build_and_deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd discoveryPortal
          npm ci
      
      - name: Build
        run: |
          cd discoveryPortal
          npm run build
      
      - name: Deploy to Firebase
        uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: '${{ secrets.GITHUB_TOKEN }}'
          firebaseServiceAccount: '${{ secrets.FIREBASE_SERVICE_ACCOUNT }}'
          channelId: live
          projectId: your-project-id
```

**Note:** Store Firebase service account credentials in GitHub Secrets.

---

## Quick Reference Commands

```bash
# Build for production
npm run build

# Deploy to Firebase Hosting
firebase deploy --only hosting

# Deploy to specific project
firebase deploy --only hosting --project your-project-id

# Create preview deployment
firebase hosting:channel:deploy preview

# List Firebase projects
firebase projects:list

# Switch Firebase project
firebase use your-project-id

# View deployment history
firebase hosting:releases:list
```

---

## Additional Resources

- [Firebase Hosting Documentation](https://firebase.google.com/docs/hosting)
- [Angular Deployment Guide](https://angular.io/guide/deployment)
- [Firebase CLI Reference](https://firebase.google.com/docs/cli)
- [Firebase Authentication Documentation](https://firebase.google.com/docs/auth)

---

## Support

For issues or questions:
1. Check the [Firebase Console](https://console.firebase.google.com) for deployment logs
2. Review browser console for client-side errors
3. Check Firebase Hosting logs in the Firebase Console
4. Refer to project-specific documentation in the repository
