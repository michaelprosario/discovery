# CLI Firebase Authentication Migration Guide

## Overview

This guide helps you migrate from the legacy API key authentication system to the new Firebase/Google Sign-In authentication.

## What's Changed

### Before (API Key Authentication)
```bash
# Initialize with API key
discovery config init --url http://localhost:8000 --api-key my-secret-key

# API key stored in config.toml
# Sent as: Authorization: Bearer <api-key>
```

### After (Firebase Authentication)
```bash
# Initialize profile
discovery config init --url http://localhost:8000

# Authenticate with Google
discovery auth login

# Firebase ID token stored in config.toml
# Sent as: Authorization: Bearer <firebase-id-token>
# Automatically refreshed when expired
```

## Benefits of Firebase Authentication

1. **Better Security**: Time-limited tokens (1 hour expiry) vs permanent API keys
2. **User Identity**: Authenticated as your Google account
3. **Automatic Refresh**: Tokens refresh automatically without re-authentication
4. **Revocable**: Can be revoked from Firebase Console
5. **Audit Trail**: Firebase tracks authentication events
6. **SSO Ready**: Can integrate with enterprise Google Workspace

## Migration Steps

### Step 1: Check Current Configuration

```bash
discovery config show
```

Look for profiles with `api_key` set.

### Step 2: Set Up Environment Variables

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Get these from Firebase Console and Google Cloud Console
export FIREBASE_WEB_API_KEY="your-firebase-web-api-key"
export GOOGLE_OAUTH_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret"
```

Reload your shell:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

### Step 3: Authenticate with Firebase

For each profile:

```bash
# Default profile
discovery auth login

# Named profile
discovery auth login --profile staging
```

This will:
1. Open your browser for Google Sign-In
2. Store Firebase credentials
3. Keep the existing API key for fallback

### Step 4: Verify New Authentication

```bash
discovery auth status
```

You should see:
```
Auth Method: Firebase/Google
User Email: you@example.com
Token Status: Valid (expires in 0h 59m)
```

### Step 5: Test API Access

```bash
# Test basic connectivity
discovery config test

# Try a real command
discovery notebooks list
```

### Step 6: Remove API Keys (Optional)

Once you've verified Firebase auth works, you can remove old API keys:

**Option A: Via CLI**
```bash
# Logout removes both API key and Firebase credentials
discovery auth logout

# Then re-authenticate with Firebase only
discovery auth login
```

**Option B: Manual Edit**

Edit `~/.discovery/config.toml`:

```toml
# Before
[profiles.default]
name = "default"
url = "http://localhost:8000"
api_key = "old-api-key"  # Remove this line

# After
[profiles.default]
name = "default"
url = "http://localhost:8000"

[profiles.default.firebase_credentials]
id_token = "eyJhbGc..."
refresh_token = "AMf-vBy..."
token_expiry = "2025-12-08T15:30:00Z"
user_email = "you@example.com"
```

## Rollback Plan

If you encounter issues, you can temporarily revert to API keys:

### Temporary Rollback

```bash
# Re-add API key to profile
discovery config init --url http://localhost:8000 --api-key your-key --overwrite --no-login
```

The CLI will use the API key if Firebase credentials are not available.

### Permanent Rollback

If you need to stay on API keys:

1. Keep using `--api-key` flag when initializing profiles
2. Use `--no-login` to skip Firebase authentication
3. The old system still works but is deprecated

**Note:** API key support will be removed in a future version.

## Common Migration Scenarios

### Scenario 1: Single User, Single Environment

```bash
# Old way
discovery config init --url http://localhost:8000 --api-key dev-key

# New way
discovery config init --url http://localhost:8000
discovery auth login
```

### Scenario 2: Multiple Environments

```bash
# Old way
discovery config init --url http://localhost:8000 --api-key dev-key --profile dev
discovery config init --url https://staging.api.com --api-key staging-key --profile staging
discovery config init --url https://prod.api.com --api-key prod-key --profile prod

# New way
discovery config init --url http://localhost:8000 --profile dev
discovery auth login --profile dev

discovery config init --url https://staging.api.com --profile staging
discovery auth login --profile staging

discovery config init --url https://prod.api.com --profile prod
discovery auth login --profile prod
```

### Scenario 3: Team with Shared Config

**Old way (insecure):**
- Shared `config.toml` with API keys checked into version control
- Everyone uses same API key

**New way (secure):**
1. Share profile URLs only (no credentials):
   ```bash
   # Share this command with team
   discovery config init --url https://api.example.com --profile shared --no-login
   ```

2. Each team member authenticates individually:
   ```bash
   discovery auth login --profile shared
   ```

3. Each user has their own Firebase credentials
4. Backend can track who made which API calls

### Scenario 4: CI/CD Pipeline

**Old way:**
```yaml
# .github/workflows/test.yml
env:
  DISCOVERY_API_KEY: ${{ secrets.API_KEY }}

steps:
  - run: discovery config init --url $API_URL --api-key $DISCOVERY_API_KEY
  - run: discovery notebooks list
```

**New way (Option A - Service Account):**
```yaml
env:
  FIREBASE_SERVICE_ACCOUNT_JSON: ${{ secrets.FIREBASE_SA }}

steps:
  - run: discovery config init --url $API_URL --no-login
  # Use service account token directly with API
```

**New way (Option B - Device Flow):**
```yaml
# Store authenticated config.toml as secret
steps:
  - run: echo "${{ secrets.DISCOVERY_CONFIG }}" > ~/.discovery/config.toml
  - run: discovery notebooks list
```

## Troubleshooting Migration

### Issue: "Firebase Web API key not configured"

**Solution:**
```bash
export FIREBASE_WEB_API_KEY="your-key-from-firebase-console"
```

Get from: Firebase Console > Project Settings > General > Web API Key

### Issue: "Google OAuth credentials not configured"

**Solution:**
```bash
export GOOGLE_OAUTH_CLIENT_ID="your-id"
export GOOGLE_OAUTH_CLIENT_SECRET="your-secret"
```

Get from: Google Cloud Console > APIs & Services > Credentials

### Issue: Browser doesn't open

**Solution:** Use device flow:
```bash
discovery auth login --device-flow
```

### Issue: "Authentication service not configured" from API

**Cause:** Backend doesn't have Firebase configured.

**Solution:** Ensure backend has:
```bash
# On the API server
export FIREBASE_CREDENTIALS_PATH="/path/to/service-account.json"
# or
export FIREBASE_SERVICE_ACCOUNT_JSON='{"type": "service_account", ...}'
```

### Issue: Old commands still use API key

**Diagnosis:**
```bash
discovery auth status
```

Shows: `Auth Method: API Key (deprecated)`

**Solution:**
```bash
discovery auth login
```

This adds Firebase credentials and they take precedence.

### Issue: Token expired errors

**Auto-fix:** Tokens auto-refresh. If issues persist:
```bash
discovery auth logout
discovery auth login
```

## Validation Checklist

After migration, verify:

- [ ] `discovery auth status` shows Firebase authentication
- [ ] `discovery config test` succeeds
- [ ] `discovery notebooks list` works
- [ ] Environment variables are set correctly
- [ ] No API keys in version control
- [ ] Team members can authenticate individually
- [ ] Tokens refresh automatically

## Timeline

- **v0.2**: Firebase authentication added, API keys deprecated
- **v0.3** (planned): API keys marked for removal, warnings added
- **v0.4** (planned): API key support removed entirely

## Getting Help

If you encounter issues:

1. Check environment variables are set correctly
2. Review `docs/CLI_FIREBASE_AUTH.md` for detailed setup
3. Verify Firebase project configuration
4. Check API server logs for authentication errors
5. Try `discovery auth logout && discovery auth login` to re-authenticate

## Resources

- [CLI Firebase Auth Documentation](./CLI_FIREBASE_AUTH.md)
- [Firebase Console](https://console.firebase.google.com/)
- [Google Cloud Console](https://console.cloud.google.com/)
- [CLI README](../src/cli/README.md)
