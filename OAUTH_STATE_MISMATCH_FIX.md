# OAuth State Mismatch Error - Fix Guide

## Problem

When running `discovery auth login` in a dev container, you encountered:

```
oauthlib.oauth2.rfc6749.errors.MismatchingStateError: (mismatching_state) CSRF Warning! State not equal in request and response.
```

## Root Cause

This error occurs because:

1. **Dev Container Environment**: You're running the CLI in a VS Code dev container
2. **Browser/Server Separation**: The OAuth callback server runs inside the container, but the browser opens on your host machine
3. **State Validation Failure**: The OAuth flow's CSRF protection detects this separation as a potential security issue

## Solution

### Option 1: Use Device Flow (Recommended for Dev Containers)

Device flow is designed for exactly this scenario:

```bash
discovery auth login --device-flow
```

This will:
1. Display a URL and code in the terminal
2. You visit the URL in any browser
3. Enter the code
4. Complete authentication without browser redirects

### Option 2: Configure OAuth Credentials (Required for Both Options)

You're also missing the required OAuth credentials. Add these to `.env`:

#### Step 1: Get Firebase Web API Key

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: `discovery-notebooks`
3. Go to **Project Settings** (⚙️ icon)
4. Under **General** tab, find **Web API Key**
5. Copy the value

#### Step 2: Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your Firebase project: `discovery-notebooks`
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth client ID**
5. If prompted to configure OAuth consent screen:
   - Choose **Internal** (if using Google Workspace) or **External**
   - Fill in app name: "Discovery CLI"
   - Add your email as developer contact
   - Add scopes: `openid`, `email`, `profile`
   - Save and continue
6. Back to **Create OAuth client ID**:
   - Application type: **Desktop app**
   - Name: "Discovery CLI Desktop"
   - Click **Create**
7. Copy **Client ID** and **Client Secret**

#### Step 3: Update .env File

Edit `/workspaces/discovery/.env` and add:

```bash
# Firebase Web API Key (from Firebase Console > Project Settings)
FIREBASE_WEB_API_KEY=AIzaSy...  # Your actual key from step 1

# Google OAuth Credentials (from Google Cloud Console > Credentials)
GOOGLE_OAUTH_CLIENT_ID=123456789-xxxxxxx.apps.googleusercontent.com  # From step 2
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxx  # From step 2
```

## Complete Setup Steps

1. **Configure OAuth Credentials** (see Option 2 above)

2. **Load environment variables**:
   ```bash
   source .env
   # Or restart your terminal/shell
   ```

3. **Authenticate using device flow**:
   ```bash
   discovery auth login --device-flow
   ```

4. **Verify authentication**:
   ```bash
   discovery auth status
   ```

   Expected output:
   ```
   Profile: default
   API URL: [your API URL]
   Auth Method: Firebase/Google
   User Email: your@email.com
   Token Status: Valid (expires in 0h 55m)
   ```

## What Was Fixed

1. **Enhanced Error Handling**: Updated `src/cli/firebase_client.py` to detect OAuth state mismatch errors and suggest device flow
2. **Documentation**: Added dev container troubleshooting to `docs/CLI_FIREBASE_AUTH.md`
3. **Environment Template**: Added commented OAuth credential placeholders to `.env`

## Testing the Fix

After configuring credentials:

```bash
# This should now show a helpful error message if it fails
discovery auth login

# This should work reliably in dev containers
discovery auth login --device-flow
```

## Why Device Flow Works

Device flow:
- ✅ No browser redirects required
- ✅ Works in SSH, containers, VMs
- ✅ Browser runs anywhere (host, phone, different computer)
- ✅ More secure for headless environments
- ✅ No state management issues

## For Future Reference

When working in dev containers or remote environments, always use:

```bash
discovery auth login --device-flow
```

Regular browser-based flow works best on:
- Local machines (not in containers)
- Direct desktop installations
- Environments where browser and server run in same context

## Related Documentation

- Full authentication guide: `docs/CLI_FIREBASE_AUTH.md`
- Firebase setup: `FIREBASE_CLI_AUTH_SUMMARY.md`
- CLI README: `src/cli/README.md`
