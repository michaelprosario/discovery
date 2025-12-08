# Discovery CLI Firebase Auth - Quick Reference

## Environment Setup

```bash
# Required environment variables
export FIREBASE_WEB_API_KEY="AIzaSy..."
export GOOGLE_OAUTH_CLIENT_ID="123456789-xxx.apps.googleusercontent.com"
export GOOGLE_OAUTH_CLIENT_SECRET="GOCSPX-xxx"
```

## Quick Start

```bash
# 1. Initialize profile
discovery config init --url https://api.example.com

# 2. Authenticate
discovery auth login

# 3. Verify
discovery auth status

# 4. Use the CLI
discovery notebooks list
```

## Authentication Commands

### Login
```bash
# Standard login (opens browser)
discovery auth login

# Login to specific profile
discovery auth login --profile staging

# Device flow for headless/SSH
discovery auth login --device-flow
```

### Status
```bash
# Check auth status
discovery auth status

# Check specific profile
discovery auth status --profile prod
```

### Refresh Token
```bash
# Manual refresh (usually automatic)
discovery auth refresh

# Refresh specific profile
discovery auth refresh --profile staging
```

### Logout
```bash
# Logout from current profile
discovery auth logout

# Logout from specific profile
discovery auth logout --profile prod
```

## Profile Management

### Create Profiles
```bash
# Development
discovery config init --url http://localhost:8000 --profile dev
discovery auth login --profile dev

# Staging
discovery config init --url https://staging.api.com --profile staging
discovery auth login --profile staging

# Production
discovery config init --url https://prod.api.com --profile prod
discovery auth login --profile prod
```

### Switch Profiles
```bash
# Set active profile
discovery config use staging

# Or use --profile flag
discovery notebooks list --profile prod
```

### View Profiles
```bash
discovery config show
```

## Common Tasks

### First Time Setup
```bash
# 1. Set environment variables in ~/.bashrc or ~/.zshrc
export FIREBASE_WEB_API_KEY="your-key"
export GOOGLE_OAUTH_CLIENT_ID="your-client-id"
export GOOGLE_OAUTH_CLIENT_SECRET="your-secret"

# 2. Reload shell
source ~/.bashrc

# 3. Initialize and authenticate
discovery config init --url https://api.example.com
discovery auth login
```

### Daily Use
```bash
# Commands automatically use your credentials
discovery notebooks list
discovery sources add url --url https://example.com
discovery qa ask --question "What is this about?"

# Tokens auto-refresh, no action needed
```

### Check If Authenticated
```bash
discovery auth status
# Look for: "Token Status: Valid"
```

### Re-authenticate
```bash
discovery auth logout
discovery auth login
```

### Headless Server
```bash
# Use device flow
discovery auth login --device-flow

# Follow the displayed instructions:
# 1. Visit the URL shown
# 2. Enter the code
# 3. Sign in with Google
```

## Troubleshooting

### "Firebase Web API key not configured"
```bash
export FIREBASE_WEB_API_KEY="your-api-key"
```

### "Google OAuth credentials not configured"
```bash
export GOOGLE_OAUTH_CLIENT_ID="your-client-id"
export GOOGLE_OAUTH_CLIENT_SECRET="your-secret"
```

### Browser doesn't open
```bash
discovery auth login --device-flow
```

### Token expired errors
```bash
# Automatic refresh should handle this
# If issues persist:
discovery auth logout
discovery auth login
```

### Backend error: "Authentication service not configured"
```bash
# Backend needs Firebase setup
# Contact your administrator
```

## Security Tips

```bash
# Set restrictive permissions on config file
chmod 600 ~/.discovery/config.toml
chmod 700 ~/.discovery

# Logout on shared machines
discovery auth logout

# Each user should authenticate individually
# Don't share config.toml files
```

## Migration from API Keys

```bash
# Old way
discovery config init --url http://localhost:8000 --api-key my-key

# New way
discovery config init --url http://localhost:8000
discovery auth login

# Both work, but API keys are deprecated
```

## Help & Documentation

```bash
# CLI help
discovery --help
discovery auth --help

# Command-specific help
discovery auth login --help
discovery auth status --help
```

## Documentation Files

- **Setup Guide**: `docs/CLI_FIREBASE_AUTH.md`
- **Migration Guide**: `docs/CLI_AUTH_MIGRATION.md`
- **Implementation Details**: `docs/CLI_FIREBASE_AUTH_IMPLEMENTATION.md`
- **CLI README**: `src/cli/README.md`

## Common Workflows

### Team Onboarding
```bash
# Share these commands (without credentials)
discovery config init --url https://api.example.com --no-login

# Each team member authenticates
discovery auth login
```

### Multiple Environments
```bash
# Setup all profiles
for env in dev staging prod; do
  discovery config init --url https://${env}.api.com --profile ${env}
  discovery auth login --profile ${env}
done

# Switch between them
discovery config use dev
discovery config use prod
```

### Script Template
```bash
#!/bin/bash
set -e

# Check authentication
if ! discovery auth status &>/dev/null; then
    echo "Not authenticated. Run: discovery auth login"
    exit 1
fi

# Your commands here
discovery notebooks list --format json
```

## Status Output Examples

### Authenticated (Valid)
```
Profile: default
API URL: https://api.example.com
Auth Method: Firebase/Google
User Email: you@example.com
Token Status: Valid (expires in 0h 45m)
```

### Not Authenticated
```
Profile: default
API URL: https://api.example.com
Auth Method: Not authenticated
Run 'discovery auth login' to authenticate
```

### Token Expired (Will Auto-Refresh)
```
Profile: default
API URL: https://api.example.com
Auth Method: Firebase/Google
User Email: you@example.com
Token Status: Expired (will auto-refresh)
```

## Configuration File Example

`~/.discovery/config.toml`:
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

## Key Points

✓ Tokens auto-refresh - no manual action needed
✓ Use `--device-flow` for headless environments  
✓ Each user authenticates individually
✓ Tokens expire after 1 hour
✓ Logout clears credentials
✓ API keys still work but are deprecated
✓ All commands respect `--profile` flag

## Need Help?

1. Check `discovery auth --help`
2. Review docs in `docs/` folder
3. Verify environment variables are set
4. Check Firebase project configuration
