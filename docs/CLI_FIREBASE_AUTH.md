# CLI Firebase Authentication Guide

## Overview

The Discovery CLI now supports Firebase-based authentication using Google Sign-In. This provides secure, token-based authentication that integrates seamlessly with the Discovery API's Firebase authentication system.

## Prerequisites

### 1. Firebase Project Setup

You need a Firebase project with Authentication enabled:

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project (or create a new one)
3. Enable **Authentication** > **Sign-in method** > **Google**
4. Note your **Web API Key** from Project Settings

### 2. Google Cloud OAuth Setup

Set up OAuth 2.0 credentials for the CLI:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your Firebase project
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth client ID**
5. Choose **Desktop app** as the application type
6. Download the JSON file or copy the Client ID and Client Secret

### 3. Environment Configuration

Set the following environment variables:

```bash
# Firebase Web API Key (from Firebase Console > Project Settings)
export FIREBASE_WEB_API_KEY="AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# Google OAuth Credentials (from Google Cloud Console)
export GOOGLE_OAUTH_CLIENT_ID="123456789-xxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com"
export GOOGLE_OAUTH_CLIENT_SECRET="GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx"
```

Add these to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) for persistence.

## Quick Start

### 1. Initialize a Profile

```bash
discovery config init --url https://your-api.example.com
```

This creates a profile without credentials. Use `--no-login` to skip automatic authentication.

### 2. Authenticate

```bash
discovery auth login
```

This will:
1. Open your default browser
2. Prompt you to sign in with Google
3. Request permission to access your email and profile
4. Store the Firebase credentials securely in `~/.discovery/config.toml`

### 3. Verify Authentication

```bash
discovery auth status
```

Output:
```
Profile: default
API URL: https://your-api.example.com
Auth Method: Firebase/Google
User Email: you@example.com
Token Status: Valid (expires in 0h 55m)
```

### 4. Start Using the CLI

```bash
discovery notebooks list
discovery sources add url --url https://example.com --notebook <id>
```

All commands automatically use your Firebase credentials.

## Authentication Commands

### `discovery auth login`

Authenticate using Google Sign-In.

**Options:**
- `--profile, -p`: Profile to authenticate (default: active profile)
- `--device-flow`: Use device flow for headless environments

**Examples:**

```bash
# Standard login (opens browser)
discovery auth login

# Login to specific profile
discovery auth login --profile staging

# Device flow for SSH/headless
discovery auth login --device-flow
```

**Device Flow:**

When using `--device-flow`, you'll see:
```
Visit this URL: https://www.google.com/device
Enter code: XXXX-XXXX
```

1. Open the URL in any browser
2. Enter the displayed code
3. Sign in with Google
4. Return to the CLI

### `discovery auth status`

Show current authentication status.

**Options:**
- `--profile, -p`: Profile to check

**Example:**

```bash
discovery auth status --profile production
```

**Output:**
```
Profile: production
API URL: https://prod-api.example.com
Auth Method: Firebase/Google
User Email: admin@example.com
Token Status: Valid (expires in 0h 45m)
```

### `discovery auth refresh`

Manually refresh your Firebase token.

**Options:**
- `--profile, -p`: Profile to refresh

**Example:**

```bash
discovery auth refresh
```

**Note:** Tokens are automatically refreshed when needed. This command is rarely required.

### `discovery auth logout`

Clear authentication credentials.

**Options:**
- `--profile, -p`: Profile to logout

**Example:**

```bash
discovery auth logout --profile staging
```

This removes credentials from the profile but keeps the profile configuration.

## Multi-Profile Usage

### Creating Multiple Profiles

```bash
# Development
discovery config init --url http://localhost:8000 --profile dev
discovery auth login --profile dev

# Staging
discovery config init --url https://staging-api.example.com --profile staging
discovery auth login --profile staging

# Production
discovery config init --url https://prod-api.example.com --profile prod
discovery auth login --profile prod
```

### Switching Profiles

```bash
# Set active profile
discovery config use staging

# Or use --profile flag
discovery notebooks list --profile prod
```

### Viewing All Profiles

```bash
discovery config show
```

Output:
```
┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ profile ┃ url                       ┃ api_key   ┃ default_notebook ┃ active ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ dev     │ http://localhost:8000     │           │                  │ yes    │
│ staging │ https://staging.api.com   │           │                  │        │
│ prod    │ https://prod.api.com      │           │                  │        │
└─────────┴───────────────────────────┴───────────┴──────────────────┴────────┘
```

## Token Management

### Automatic Refresh

Tokens are automatically refreshed when:
- They are expired or will expire within 5 minutes
- An API call returns a 401 Unauthorized error

You typically don't need to manually refresh tokens.

### Token Expiry

Firebase ID tokens expire after 1 hour. The CLI:
1. Tracks expiry time
2. Automatically refreshes before expiration
3. Updates stored credentials

### Manual Refresh

If you encounter authentication issues:

```bash
discovery auth refresh
```

### Token Storage

Tokens are stored in `~/.discovery/config.toml`:

```toml
active_profile = "default"

[profiles.default]
name = "default"
url = "https://api.example.com"

[profiles.default.firebase_credentials]
id_token = "eyJhbGc..."
refresh_token = "AMf-vBy..."
token_expiry = "2025-12-08T15:30:00Z"
user_email = "you@example.com"
```

**Security:** Ensure this file has proper permissions:

```bash
chmod 600 ~/.discovery/config.toml
```

## Troubleshooting

### "Firebase Web API key not configured"

**Solution:** Set the `FIREBASE_WEB_API_KEY` environment variable:

```bash
export FIREBASE_WEB_API_KEY="your-api-key"
```

Get this from Firebase Console > Project Settings > Web API Key.

### "Google OAuth credentials not configured"

**Solution:** Set OAuth credentials:

```bash
export GOOGLE_OAUTH_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret"
```

Get these from Google Cloud Console > Credentials.

### Browser Doesn't Open

**Try device flow:**

```bash
discovery auth login --device-flow
```

### OAuth State Mismatch Error

**Error:** `MismatchingStateError: (mismatching_state) CSRF Warning! State not equal in request and response`

**Cause:** This commonly occurs when running in dev containers, remote environments, or behind proxies where the browser (running on the host) and the OAuth callback server (running in the container) are in different contexts.

**Solution:** Use device flow authentication instead:

```bash
discovery auth login --device-flow
```

Device flow doesn't require browser redirects and works reliably in:
- Dev containers (VS Code Remote Containers, GitHub Codespaces)
- SSH sessions
- Virtual machines
- Docker containers
- Any headless or remote environment

### "Authentication service not configured" (API Error)

This means the backend doesn't have Firebase configured. Ensure:

1. Backend has `FIREBASE_CREDENTIALS_PATH` or `FIREBASE_SERVICE_ACCOUNT_JSON` set
2. Firebase Admin SDK is initialized
3. The service account has proper permissions

### Token Refresh Failures

If refresh fails repeatedly:

1. Logout and login again:
   ```bash
   discovery auth logout
   discovery auth login
   ```

2. Check your internet connection
3. Verify Firebase project is active
4. Check token hasn't been revoked in Firebase Console

### Multiple CLI Sessions

The CLI handles concurrent sessions safely:
- Config file updates use atomic writes
- Token refresh is synchronized
- Each command gets the latest credentials

## Security Best Practices

### 1. Protect Configuration Files

```bash
# Set restrictive permissions
chmod 600 ~/.discovery/config.toml
chmod 700 ~/.discovery
```

### 2. Don't Share Credentials

- Never commit config files to version control
- Don't share your `config.toml` file
- Each user should authenticate individually

### 3. Logout When Done

On shared machines:

```bash
discovery auth logout
```

### 4. Use Environment-Specific Profiles

Don't reuse production credentials in development:

```bash
# Separate profiles for each environment
discovery config init --profile dev --url http://localhost:8000
discovery config init --profile prod --url https://prod.api.com
```

### 5. Rotate Credentials Regularly

Periodically logout and re-authenticate:

```bash
discovery auth logout
discovery auth login
```

## CI/CD Integration

### Service Accounts (Recommended)

For automated workflows, use Firebase service accounts instead of user authentication:

1. Create a service account in Firebase Console
2. Download the service account JSON
3. Set `FIREBASE_SERVICE_ACCOUNT_JSON` in your CI environment
4. Use API endpoints that accept service account tokens

### Device Flow (Alternative)

If you must use user credentials:

```bash
discovery auth login --device-flow
```

Store the resulting `config.toml` as a CI secret.

**Warning:** This is less secure than service accounts.

## Migration from API Keys

### Automatic Detection

The CLI detects API key profiles:

```bash
discovery auth status
```

Output:
```
Auth Method: API Key (deprecated)
```

### Migration Steps

1. Authenticate with Firebase:
   ```bash
   discovery auth login
   ```

2. Verify new credentials:
   ```bash
   discovery auth status
   ```

3. The profile now uses Firebase instead of API keys

### Removing API Keys

API keys are kept for backwards compatibility but ignored when Firebase credentials exist. To remove:

1. Edit `~/.discovery/config.toml`
2. Remove `api_key` field from profile
3. Or re-initialize the profile:
   ```bash
   discovery config init --url <url> --overwrite
   discovery auth login
   ```

## Advanced Usage

### Custom Configuration Location

```bash
export DISCOVERY_CONFIG_HOME="/custom/path"
discovery config init --url https://api.example.com
discovery auth login
```

### Scripting Authentication

For scripts, check authentication before running:

```bash
#!/bin/bash
set -e

# Check auth status
if ! discovery auth status --profile prod &>/dev/null; then
    echo "Not authenticated. Please run: discovery auth login --profile prod"
    exit 1
fi

# Run commands
discovery notebooks list --profile prod --format json
```

### Debugging

Enable verbose output:

```bash
# Set HTTPX_LOG_LEVEL for HTTP debugging
export HTTPX_LOG_LEVEL=debug
discovery notebooks list
```

## API Reference

See the backend Firebase authentication documentation:
- Backend implementation: `src/api/auth/firebase_auth.py`
- API documentation: `docs/API_CONFIGURATION.md`
- Firebase setup: `FIREBASE_IMPLEMENTATION_SUMMARY.md`

## Support

For issues or questions:
1. Check `discovery --help` and `discovery auth --help`
2. Review this documentation
3. Check API logs for authentication errors
4. Verify Firebase project configuration
