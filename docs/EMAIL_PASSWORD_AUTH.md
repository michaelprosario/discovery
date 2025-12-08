# Email/Password Authentication - Implementation Summary

## Overview

Added email/password authentication as the **primary and recommended** authentication method for the Discovery CLI. This provides a simple, user-friendly way to authenticate without requiring OAuth credentials.

## What Changed

### New Features

1. **Email/Password Sign Up**
   ```bash
   discovery auth signup
   ```
   - Creates new Firebase account
   - Prompts for email and password
   - Confirms password
   - Automatically logs in after signup

2. **Email/Password Login**
   ```bash
   discovery auth login-email
   ```
   - Logs in with existing account
   - Prompts for credentials
   - Supports flags for scripting: `--email` and `--password`

3. **Password Reset**
   ```bash
   discovery auth reset-password
   ```
   - Sends password reset email
   - Uses Firebase's built-in password reset flow

### Environment Variables

**Required:**
- `FIREBASE_WEB_API_KEY` - Firebase Web API key from console

**Optional (only for Google Sign-In):**
- `GOOGLE_OAUTH_CLIENT_ID` - No longer required for basic usage
- `GOOGLE_OAUTH_CLIENT_SECRET` - No longer required for basic usage

## Files Created

1. **`src/cli/firebase_email_auth.py`** (238 lines)
   - `FirebaseEmailAuthClient` class
   - Email/password sign in
   - Account creation (sign up)
   - Token refresh
   - Password reset
   - User-friendly error messages

2. **`tests/cli/test_firebase_email_auth.py`** (265 lines)
   - Comprehensive test coverage
   - Sign in/up tests
   - Error handling tests
   - Password reset tests
   - Network error tests

## Files Modified

1. **`src/cli/commands/auth.py`**
   - Added `login-email` command
   - Added `signup` command  
   - Added `reset-password` command
   - Interactive prompts for credentials
   - Support for command-line flags

2. **`src/cli/firebase_client.py`**
   - Updated `refresh_token()` to use `FirebaseEmailAuthClient`
   - Simplified token refresh logic

3. **`src/cli/README.md`**
   - Updated authentication section
   - Marked OAuth credentials as optional
   - Email/password listed as recommended method

4. **`docs/CLI_AUTH_QUICKREF.md`**
   - Added email/password examples
   - Updated environment variables section
   - Reorganized authentication methods

## User Experience

### Before (OAuth Required)
```bash
# Required: Set up OAuth credentials
export FIREBASE_WEB_API_KEY="..."
export GOOGLE_OAUTH_CLIENT_ID="..."
export GOOGLE_OAUTH_CLIENT_SECRET="..."

# Login opens browser
discovery config init --url https://api.example.com
discovery auth login  # Opens browser for Google Sign-In
```

### After (Email/Password - Simple)
```bash
# Required: Only Firebase Web API key
export FIREBASE_WEB_API_KEY="..."

# Simple signup/login
discovery config init --url https://api.example.com
discovery auth signup
# Email: user@example.com
# Password: ••••••••
# Confirm password: ••••••••
```

## Benefits

1. **Simpler Setup**
   - Only 1 environment variable required (vs 3)
   - No OAuth configuration needed
   - No Google Cloud Console setup

2. **Better User Experience**
   - Interactive prompts
   - Password confirmation on signup
   - Friendly error messages
   - Password reset functionality

3. **More Secure**
   - Each user has individual account
   - Passwords managed by Firebase
   - Password reset via email
   - Rate limiting built-in

4. **Script-Friendly**
   - Supports `--email` and `--password` flags
   - Non-interactive mode for automation
   - Same token management as OAuth

## Firebase Setup Required

Enable email/password authentication in Firebase Console:

1. Go to Firebase Console > Authentication
2. Click "Sign-in method"
3. Enable "Email/Password"
4. Save

That's it! No OAuth configuration needed.

## Error Messages

Friendly error messages for common issues:

| Firebase Error | User-Friendly Message |
|----------------|----------------------|
| EMAIL_NOT_FOUND | No account found with this email address |
| INVALID_PASSWORD | Incorrect password |
| USER_DISABLED | This account has been disabled |
| EMAIL_EXISTS | An account with this email already exists |
| WEAK_PASSWORD | Password is too weak (minimum 6 characters) |
| INVALID_EMAIL | Invalid email address |
| TOO_MANY_ATTEMPTS_TRY_LATER | Too many failed attempts. Please try again later |

## Usage Examples

### New User Signup
```bash
discovery config init --url https://api.example.com
discovery auth signup
# Email: newuser@example.com
# Password: securepass123
# Confirm password: securepass123
# ✓ Account created and authenticated as newuser@example.com
```

### Existing User Login
```bash
discovery auth login-email
# Email: user@example.com
# Password: ••••••••
# ✓ Successfully authenticated as user@example.com
```

### Forgot Password
```bash
discovery auth reset-password
# Email: user@example.com
# ✓ Password reset email sent to user@example.com
# Check your inbox and follow the instructions to reset your password.
```

### Script/Automation
```bash
# Non-interactive login
discovery auth login-email \
  --email user@example.com \
  --password $MY_PASSWORD
```

## Backwards Compatibility

- ✅ OAuth login still works (`discovery auth login`)
- ✅ API key authentication still works
- ✅ Existing tokens continue to work
- ✅ All token refresh logic unified

## Recommendation for Users

**For individual users accessing a shared Discovery instance:**
1. Use email/password authentication
2. Each user creates their own account
3. Instance owner manages users via Firebase Console

**For OAuth/Google Sign-In:**
1. Only if users want to use their Google accounts
2. Requires additional OAuth setup
3. Better for enterprise SSO scenarios

## Testing

```bash
# Run email auth tests
pytest tests/cli/test_firebase_email_auth.py -v

# Run all auth tests
pytest tests/cli/test_firebase*.py -v
```

## Next Steps

1. ✅ Email/password authentication implemented
2. ✅ Tests written and passing
3. ✅ Documentation updated
4. Future: Add user management commands for admins
5. Future: Add email verification flow
6. Future: Add profile management (change email/password)

## Summary

Email/password authentication is now the **recommended** authentication method for the Discovery CLI. It provides a simpler, more user-friendly experience while maintaining security and flexibility. OAuth/Google Sign-In remains available for advanced use cases.
