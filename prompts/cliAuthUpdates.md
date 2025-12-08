# CLI Firebase Authentication Implementation Plan

## Overview

This document outlines the implementation plan for adding Firebase/Google authentication support to the Discovery CLI. This will enable CLI users to authenticate using their Google credentials and securely interact with Firebase-protected Discovery API instances. This replaces the existing API key authentication system with Firebase-based authentication.

## Current State Analysis

### Existing CLI Architecture
- **Location**: `src/cli/`
- **Framework**: Typer (Python CLI framework)
- **HTTP Client**: `httpx` with custom wrapper (`DiscoveryApiClient`)
- **Authentication**: Currently uses API key-based authentication (to be replaced)
  - API keys stored in `~/.discovery/config.toml`
  - Headers: `Authorization: Bearer {api_key}` and `X-API-Key: {api_key}`
- **Configuration**: Profile-based system supporting multiple environments
- **Storage**: `ConfigStore` manages profiles and state

### Backend Firebase Integration
- **Location**: `src/api/auth/firebase_auth.py`
- **Token Verification**: Uses `firebase-admin` SDK
- **Token Format**: Firebase ID tokens in `Authorization: Bearer {id_token}` header
- **User Identification**: Extracts email from verified tokens

## Requirements

### User Stories
1. **As a CLI user**, I want to authenticate using my Google account so I can securely access the Discovery API
2. **As a CLI user**, I want the CLI to manage my authentication tokens automatically so I don't have to handle them manually
3. **As a CLI user**, I want my session to persist across CLI invocations so I don't have to re-authenticate frequently
4. **As a CLI user**, I want to easily switch between different authenticated profiles for different environments

### Technical Requirements
- Support Google Sign-In flow for CLI applications
- Store and refresh Firebase ID tokens automatically
- Secure token storage in local configuration
- Token refresh before expiration
- Clear error messages for authentication failures

## Implementation Plan

### Phase 1: Firebase Client SDK Integration

#### 1.1 Dependencies
**File**: `pyproject.toml`
- Add Firebase client SDK dependencies:
  - `firebase` or `firebase-admin` (for token management)
  - `google-auth` (for Google OAuth flow)
  - `google-auth-oauthlib` (for interactive OAuth)

#### 1.2 Firebase Configuration Module
**New File**: `src/cli/firebase_client.py`

Features:
- Initialize Firebase client SDK
- Handle Google OAuth 2.0 flow for CLI (device flow or localhost callback)
- Obtain Firebase ID tokens from Google credentials
- Refresh expired tokens
- Validate token expiration

```python
class FirebaseAuthClient:
    """Manages Firebase authentication for CLI."""
    
    def login() -> FirebaseCredentials:
        """Initiate Google Sign-In and return Firebase credentials."""
        
    def refresh_token() -> str:
        """Refresh an expired Firebase ID token."""
        
    def get_valid_token() -> str:
        """Get current token, refreshing if necessary."""
        
    def logout() -> None:
        """Clear stored credentials."""
```

### Phase 2: Configuration Schema Updates

#### 2.1 Update Profile Model
**File**: `src/cli/config_store.py`

Simplify `DiscoveryProfile` to use only Firebase authentication:

```python
class DiscoveryProfile(BaseModel):
    name: str
    url: AnyHttpUrl
    firebase_credentials: FirebaseCredentials | None = None
    default_notebook: str | None = None

class FirebaseCredentials(BaseModel):
    """Firebase authentication credentials."""
    id_token: str
    refresh_token: str
    token_expiry: datetime
    user_email: str
```

**Migration Note**: Remove `api_key` field from existing profiles during upgrade.

#### 2.2 Secure Storage Considerations
- Store refresh tokens in `~/.discovery/config.toml` (or separate secure file)
- Set appropriate file permissions (0600) for config files
- Consider using keyring library for OS-level credential storage (optional enhancement)

### Phase 3: HTTP Client Updates

#### 3.1 Update DiscoveryApiClient
**File**: `src/cli/http_client.py`

Modify to use Firebase authentication exclusively:

```python
class DiscoveryApiClient:
    def __init__(self, profile: DiscoveryProfile, ...):
        headers = self._build_auth_headers(profile)
        # ... rest of initialization
    
    def _build_auth_headers(self, profile: DiscoveryProfile) -> Dict[str, str]:
        """Build authentication headers with Firebase token."""
        token = self._get_firebase_token(profile)
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "discovery-cli/0.2",
        }
    
    def _get_firebase_token(self, profile: DiscoveryProfile) -> str:
        """Get valid Firebase token, refreshing if needed."""
        if not profile.firebase_credentials:
            raise AuthenticationError(
                "Not authenticated. Run 'discovery auth login' to authenticate."
            )
        # Check expiry, refresh if needed
        # Update profile with new token
        # Return valid ID token
```

### Phase 4: Authentication Commands

#### 4.1 New Auth Command Group
**New File**: `src/cli/commands/auth.py`

```python
auth_app = typer.Typer(help="Manage authentication.")

@auth_app.command("login")
def login_firebase(
    profile: str = typer.Option("default", "--profile", "-p"),
) -> None:
    """Authenticate using Google Sign-In."""
    # 1. Initiate Google OAuth flow
    # 2. Obtain Firebase ID token
    # 3. Store credentials in profile
    # 4. Verify connectivity with backend
    
@auth_app.command("logout")
def logout(
    profile: str = typer.Option("default", "--profile", "-p"),
) -> None:
    """Clear authentication credentials."""
    
@auth_app.command("status")
def auth_status(
    profile: str = typer.Option("default", "--profile", "-p"),
) -> None:
    """Show current authentication status."""
    # Display: auth method, user email, token expiry
    
@auth_app.command("refresh")
def refresh_token(
    profile: str = typer.Option("default", "--profile", "-p"),
) -> None:
    """Manually refresh Firebase token."""
```

#### 4.2 Register Auth Commands
**File**: `src/cli/__main__.py`

```python
from .commands.auth import auth_app

app.add_typer(auth_app, name="auth", help="Manage authentication.")
```

### Phase 5: Update Config Commands

#### 5.1 Update config init
**File**: `src/cli/commands/config.py`

Simplify to require Firebase authentication:

```python
@config_app.command("init")
def init_config(
    url: str = typer.Option(...),
    profile: str = typer.Option("default", "--profile", "-p"),
    login: bool = typer.Option(
        True, 
        "--login/--no-login",
        help="Authenticate after creating profile"
    ),
    # ... other options
) -> None:
    """Initialize a new CLI profile."""
    # Create profile without credentials
    profile_model = DiscoveryProfile(name=profile, url=url)
    store.upsert_profile(profile_model, make_active=True)
    
    if login:
        # Trigger authentication flow
        console.print("Starting authentication...")
        # Call auth login logic
```

### Phase 6: OAuth Flow Implementation

#### 6.1 Choose OAuth Flow Strategy

**Option A: Local Redirect Flow** (Recommended)
- Start local HTTP server on `localhost:8080` (or random port)
- Open browser to Google OAuth consent screen
- Redirect back to localhost after authentication
- Better UX, more familiar to users

**Option B: Device Flow**
- Display a code to user
- User navigates to Google URL and enters code
- CLI polls for completion
- Better for headless/SSH environments

**Implementation**: Support both with `--device-flow` flag

#### 6.2 Firebase/Google OAuth Integration

Use one of these approaches:

**Approach 1: Firebase REST API** (Recommended for CLI)
```python
# 1. Get Google OAuth token using google-auth-oauthlib
# 2. Exchange for Firebase ID token using Firebase REST API
#    POST https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp
# 3. Manage token refresh via REST API
```

**Approach 2: Firebase Client SDK**
```python
# Use Firebase Python client library (if available for ID token flow)
# May require firebase-admin for token operations
```

### Phase 7: Testing & Documentation

#### 7.1 Testing
**New File**: `tests/cli/test_firebase_auth.py`
- Test Firebase token acquisition flow (mocked)
- Test token refresh logic
- Test API calls with Firebase tokens
- Test error handling (expired tokens, revoked tokens)
- Test profile switching between auth methods

#### 7.2 Documentation Updates

**Update**: `src/cli/README.md`
```markdown
## Authentication

All authentication is handled through Firebase/Google Sign-In.

### Initial Setup
# Initialize profile
discovery config init --url https://api.example.com

# Authenticate with Google (opens browser)
discovery auth login

### Authentication Commands
# Check authentication status
discovery auth status

# Refresh token manually (usually automatic)
discovery auth refresh

# Logout
discovery auth logout

### Switching Profiles
# Create and login to a new profile
discovery config init --url https://api.staging.com --profile staging
discovery auth login --profile staging

# Use specific profile for commands
discovery notebooks list --profile staging
```

**New**: `docs/CLI_FIREBASE_AUTH.md`
- Detailed setup guide
- Firebase project configuration
- Troubleshooting common issues
- Security best practices

## Implementation Phases & Timeline

### Phase 1: Foundation (Week 1)
- [ ] Add dependencies to pyproject.toml
- [ ] Create `firebase_client.py` module
- [ ] Implement basic OAuth flow (local redirect)
- [ ] Test OAuth flow in isolation

### Phase 2: Configuration (Week 1-2)
- [ ] Update `DiscoveryProfile` model
- [ ] Add `FirebaseCredentials` model
- [ ] Update config storage/loading
- [ ] Implement secure file permissions

### Phase 3: HTTP Integration (Week 2)
- [ ] Update `DiscoveryApiClient` for Firebase tokens
- [ ] Implement token refresh logic
- [ ] Test API calls with Firebase tokens

### Phase 4: Commands (Week 2-3)
- [ ] Create `auth` command group
- [ ] Implement `auth login`
- [ ] Implement `auth logout`
- [ ] Implement `auth status`
- [ ] Implement `auth refresh`
- [ ] Update `config init` for auth methods

### Phase 5: Testing & Polish (Week 3)
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Update documentation
- [ ] Test migration from API key to Firebase auth
- [ ] Test multi-profile scenarios

### Phase 6: Advanced Features (Week 4)
- [ ] Implement device flow for headless environments
- [ ] Add keyring support for secure storage (optional)
- [ ] Implement automatic token refresh on API calls
- [ ] Add auth status to `config show`

## Security Considerations

1. **Token Storage**
   - Store refresh tokens, not just ID tokens
   - Set file permissions to 0600 on config files
   - Consider OS keyring integration for production

2. **Token Transmission**
   - Always use HTTPS for API calls
   - Never log tokens
   - Clear tokens from memory after use

3. **Token Lifecycle**
   - Implement automatic refresh before expiration
   - Handle token revocation gracefully
   - Provide clear logout mechanism

4. **Error Handling**
   - Clear error messages for auth failures
   - Don't expose sensitive details in errors
   - Guide users to re-authenticate when needed

## Migration from API Key Authentication

### Breaking Change Notice
This is a **breaking change** that replaces API key authentication with Firebase authentication.

### Migration Steps for Existing Users

1. **Automatic Migration on First Run**
   ```python
   # In ConfigStore.load()
   def load(self) -> DiscoveryConfig:
       config = self._load_from_file()
       
       # Detect old API key profiles
       for profile in config.profiles.values():
           if hasattr(profile, 'api_key') and profile.api_key:
               console.print(
                   f"[yellow]Profile '{profile.name}' uses deprecated API key auth.[/yellow]"
               )
               console.print("Please re-authenticate with: discovery auth login")
       
       return config
   ```

2. **Manual Migration Command**
   ```bash
   # Users upgrade and re-authenticate
   discovery auth login --profile default
   ```

3. **Documentation**
   - Add migration guide to CHANGELOG.md
   - Update README.md with new auth flow
   - Provide clear upgrade instructions

## Edge Cases to Handle

1. **Expired Tokens During Command Execution**
   - Auto-refresh and retry request
   - Fall back to prompting for re-authentication

2. **Network Failures During OAuth**
   - Timeout handling
   - Retry mechanism
   - Clear error messages

3. **Multiple Profiles with Same User**
   - Allow same user across different API endpoints
   - Each profile maintains separate token storage

4. **Token Revocation**
   - Detect revoked tokens (401 errors)
   - Auto-trigger re-authentication flow

5. **Concurrent CLI Invocations**
   - File locking for config updates
   - Handle race conditions in token refresh

## Future Enhancements

1. **SSO Support**
   - SAML integration
   - Enterprise OAuth providers

2. **Biometric Authentication**
   - OS-level biometric verification before token use

3. **Session Management**
   - Multiple simultaneous sessions
   - Session timeout configuration

4. **Audit Logging**
   - Log authentication events
   - Track token refresh operations

## Dependencies Summary

### Required Python Packages
```toml
[project.dependencies]
# ... existing dependencies
google-auth = "^2.23.0"
google-auth-oauthlib = "^1.1.0"
requests = "^2.31.0"  # For Firebase REST API calls
```

### Optional Packages
```toml
[project.optional-dependencies]
secure-storage = [
    "keyring>=24.0.0",  # OS keyring integration
]
```

## Success Criteria

- [ ] CLI users can authenticate with Google credentials
- [ ] Tokens are automatically refreshed
- [ ] All existing CLI commands work with Firebase auth
- [ ] Clear documentation for setup and usage
- [ ] Comprehensive error handling
- [ ] Migration guide for existing API key users
- [ ] Secure token storage
- [ ] Works on macOS, Linux, and Windows
- [ ] Unit test coverage > 80%
- [ ] Integration tests covering main flows

## Questions to Resolve

1. **Firebase Project Configuration**
   - Will CLI need Firebase project credentials (service account)?
   - Or use Firebase REST API with just project API key?

2. **OAuth Client ID**
   - Who provides the OAuth client ID (project maintainer or user)?
   - Should it be configurable per profile?

3. **Token Refresh Strategy**
   - Refresh on every command (safe but slower)?
   - Refresh only when near expiration (faster but requires expiry tracking)?
   - Lazy refresh on 401 errors (simplest)?

4. **Headless Environment Support**
   - Is device flow required for CI/CD?
   - Service account alternative for automation?

## References

- Firebase Authentication REST API: https://firebase.google.com/docs/reference/rest/auth
- Google OAuth 2.0: https://developers.google.com/identity/protocols/oauth2
- google-auth library: https://google-auth.readthedocs.io/
- Existing backend auth: `src/api/auth/firebase_auth.py`
- Frontend implementation: `FIREBASE_IMPLEMENTATION_SUMMARY.md`