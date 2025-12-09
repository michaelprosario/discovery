# Discovery CLI - Remove Firebase Auth and Implement API Key Authentication

## Overview
Remove all Firebase authentication from the Discovery CLI and replace it with simple API key authentication for communicating with the FastAPI backend.

## Implementation Plan

### Phase 1: Update Data Models and Configuration

#### 1.1 Update `src/cli/config_store.py`
- [ ] Remove `FirebaseCredentials` class completely
- [ ] Update `DiscoveryProfile` model:
  - Remove `firebase_credentials: FirebaseCredentials | None = None`
  - Keep `api_key: str | None = None` but make it the primary auth method (remove deprecation note)
- [ ] Update `is_authenticated` property to only check `api_key`
- [ ] Remove any Firebase-related imports

#### 1.2 Update `src/cli/http_client.py`
- [ ] Remove `_get_firebase_token()` method
- [ ] Simplify `_get_auth_header()` to only use API key:
  ```python
  def _get_auth_header(self) -> str | None:
      if self.profile.api_key:
          return f"Bearer {self.profile.api_key}"
      return None
  ```
- [ ] Remove Firebase-related imports (`firebase_client`)
- [ ] Remove token refresh logic

### Phase 2: Remove Firebase Authentication Files

#### 2.1 Delete Firebase-related modules
- [ ] Delete `src/cli/firebase_client.py`
- [ ] Delete `src/cli/firebase_email_auth.py`

#### 2.2 Delete Firebase test files
- [ ] Delete `tests/cli/test_firebase_auth.py`
- [ ] Delete `tests/cli/test_firebase_email_auth.py`

### Phase 3: Update Authentication Commands

#### 3.1 Simplify `src/cli/commands/auth.py`
- [ ] Remove all Firebase-related imports
- [ ] Remove `login_firebase()` command (Google Sign-In)
- [ ] Remove these commands:
  - `login` (Google Sign-In)
  - `signup` (Email signup)
  - `login-email` (Email login)
  - `reset-password`
  - `refresh`
- [ ] Update `logout()` command to only clear `api_key`
- [ ] Update `auth_status()` command to only show API key status (masked)
- [ ] Add new simple `set-api-key` command:
  ```bash
  discovery auth set-api-key --key <api-key>
  ```
- [ ] Add option to set API key during profile creation

#### 3.2 Update `src/cli/commands/config.py`
- [ ] Update `config init` command to accept `--api-key` parameter
- [ ] Remove `--no-login` flag (no longer needed)
- [ ] Simplify profile creation to just store URL and API key

### Phase 4: Update Runtime and Utilities

#### 4.1 Update `src/cli/runtime.py`
- [ ] Remove any Firebase credential handling
- [ ] Ensure runtime only validates API key presence for authenticated operations

#### 4.2 Update `src/cli/utils.py`
- [ ] Remove any Firebase-related utility functions

### Phase 5: Update Documentation

#### 5.1 Update `src/cli/README.md`
- [ ] Remove all Firebase authentication sections
- [ ] Remove Google OAuth setup instructions
- [ ] Remove environment variable references:
  - Remove `FIREBASE_WEB_API_KEY`
  - Remove `GOOGLE_OAUTH_CLIENT_ID`
  - Remove `GOOGLE_OAUTH_CLIENT_SECRET`
- [ ] Simplify "Authentication" section to show API key usage:
  ```markdown
  ## Authentication
  
  The Discovery CLI uses API key authentication to communicate with the FastAPI backend.
  
  ### Setup
  
  1. Initialize your profile with API URL:
     ```bash
     discovery config init --url http://localhost:8000
     ```
  
  2. Set your API key:
     ```bash
     discovery auth set-api-key --key your-api-key-here
     ```
  
  Or combine both steps:
  ```bash
  discovery config init --url http://localhost:8000 --api-key your-api-key-here
  ```
  
  ### Multiple Profiles
  
  ```bash
  # Create profile with API key
  discovery config init --url https://api.staging.com --api-key <key> --profile staging
  
  # Use specific profile
  discovery notebooks list --profile staging
  
  # Switch active profile
  discovery config use staging
  ```
  
  ### Check Authentication Status
  
  ```bash
  discovery auth status
  ```
  ```
- [ ] Update command reference table to remove Firebase auth commands
- [ ] Update examples to show API key authentication
- [ ] Remove "Headless Environments" section
- [ ] Remove "Legacy API Key Support" section (API key is now primary method)

#### 5.2 Update main `README.md`
- [ ] Search for CLI references and update authentication instructions
- [ ] Remove Firebase authentication mentions
- [ ] Update quick start examples to use API key

#### 5.3 Update `QUICK_START.md`
- [ ] Update CLI authentication steps to use API key
- [ ] Remove Firebase setup references

### Phase 6: Update Dependencies

#### 6.1 Update `pyproject.toml`
- [ ] Remove Firebase-related dependencies:
  - `firebase-admin` (if present)
  - `google-auth`
  - `google-auth-oauthlib`
  - `google-auth-httplib2`
- [ ] Keep only essential dependencies for API key auth

### Phase 7: Testing and Validation

#### 7.1 Manual Testing
- [ ] Test `discovery config init --url <url> --api-key <key>`
- [ ] Test `discovery auth set-api-key --key <key>`
- [ ] Test `discovery auth status`
- [ ] Test `discovery auth logout`
- [ ] Test API calls with API key authentication
- [ ] Test profile switching with multiple API keys
- [ ] Verify backwards compatibility with existing config files

#### 7.2 Update Tests
- [ ] Update integration tests to use API key auth
- [ ] Remove Firebase mock/fixture tests
- [ ] Add tests for new `set-api-key` command

### Phase 8: Migration Notes

#### 8.1 Create Migration Guide
- [ ] Document how existing users should migrate from Firebase to API key
- [ ] Provide script or instructions to extract and set API keys
- [ ] Add deprecation warnings if Firebase credentials detected in config

## Environment Variables After Changes

Only these environment variables will be needed:
- `DISCOVERY_CONFIG_HOME`: Configuration directory (optional, defaults to `~/.discovery`)
- `DISCOVERY_API_URL`: API base URL (optional, for shell integration)
- `DISCOVERY_API_KEY`: API key (optional, for shell integration)
- `DISCOVERY_NOTEBOOK_GUID`: Default notebook (optional, for shell integration)

## Files to Modify

### Delete:
1. `src/cli/firebase_client.py`
2. `src/cli/firebase_email_auth.py`
3. `tests/cli/test_firebase_auth.py`
4. `tests/cli/test_firebase_email_auth.py`

### Modify:
1. `src/cli/config_store.py` - Remove FirebaseCredentials, simplify DiscoveryProfile
2. `src/cli/http_client.py` - Simplify auth to use only API key
3. `src/cli/commands/auth.py` - Remove Firebase commands, add set-api-key
4. `src/cli/commands/config.py` - Update init command for API key
5. `src/cli/runtime.py` - Remove Firebase handling
6. `src/cli/README.md` - Complete documentation rewrite
7. `README.md` - Update CLI references
8. `QUICK_START.md` - Update authentication steps
9. `pyproject.toml` - Remove Firebase dependencies

## Success Criteria

- [ ] All Firebase code removed from CLI
- [ ] Simple API key authentication working
- [ ] All commands functional with API key auth
- [ ] Documentation updated and accurate
- [ ] Tests passing
- [ ] No Firebase dependencies in pyproject.toml
- [ ] Clean migration path for existing users