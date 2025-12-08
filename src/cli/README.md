# Discovery CLI

A Typer-powered command line interface for orchestrating the Discovery research system over its FastAPI backend. The CLI enables you to configure API profiles, manage notebooks and sources, trigger vector ingestion, generate outputs, and run question answering – all from a terminal session or within shell scripts.

## Installation

```bash
# from the repository root
python -m pip install -e .

# or install into an isolated environment via pipx
pipx install path/to/discovery
```

The project publishes the console script `discovery` via the entry point declared in `pyproject.toml`.

## First Run

1. Boot the Discovery FastAPI service (e.g., `scripts/dev.sh` or Docker).
2. Point the CLI at the API by creating a profile:
   ```bash
   discovery config init --url http://localhost:8000
   ```
3. Authenticate using Google Sign-In:
   ```bash
   discovery auth login
   ```
   This will open your browser for Google authentication and securely store your Firebase credentials.

4. Verify connectivity:
   ```bash
   discovery config test
   ```
5. List notebooks to confirm everything is wired up:
   ```bash
   discovery notebooks list
   ```

Configuration is stored in `~/.discovery/config.toml` (override with `DISCOVERY_CONFIG_HOME`). Runtime state such as the most recently used notebook GUID lives in `state.json` in the same directory.

## Authentication

All authentication is handled through Firebase for secure access to the Discovery API.

### Authentication Methods

**1. Email/Password (Recommended - Simple)**
```bash
# Create a new account
discovery auth signup

# Login with existing account
discovery auth login-email
```

**2. Google Sign-In (Requires OAuth setup)**
```bash
# Login with Google account (opens browser)
discovery auth login
```

### Initial Setup (Email/Password)

```bash
# Initialize profile (creates profile without credentials)
discovery config init --url https://api.example.com

# Create account or login
discovery auth signup  # First time
# OR
discovery auth login-email  # Subsequent logins
```

### Authentication Commands

```bash
# Email/Password Authentication
discovery auth signup              # Create new account
discovery auth login-email         # Login with email/password
discovery auth reset-password      # Send password reset email

# Google Sign-In (requires OAuth credentials)
discovery auth login               # Login with Google

# General Commands
discovery auth status              # Check authentication status
discovery auth refresh             # Refresh token manually (usually automatic)
discovery auth logout              # Logout (clear credentials)
```

### Multiple Profiles

```bash
# Create and login to a new profile
discovery config init --url https://api.staging.com --profile staging
discovery auth login --profile staging

# Use specific profile for commands
discovery notebooks list --profile staging

# Switch active profile
discovery config use staging
```

### Headless Environments

For environments without a browser (SSH, CI/CD), use device flow:

```bash
discovery auth login --device-flow
```

This will display a code to enter at a Google URL.

### Environment Setup

Required environment variable for Firebase authentication:

```bash
# Firebase Web API Key (from Firebase Console)
export FIREBASE_WEB_API_KEY="your-firebase-web-api-key"
```

**Optional** (only needed for Google Sign-In):

```bash
# Google OAuth credentials (from Google Cloud Console) - OPTIONAL
export GOOGLE_OAUTH_CLIENT_ID="your-oauth-client-id.apps.googleusercontent.com"
export GOOGLE_OAUTH_CLIENT_SECRET="your-oauth-client-secret"
```

### Legacy API Key Support

API key authentication is deprecated but still supported for backwards compatibility:

```bash
discovery config init --url http://localhost:8000 --api-key test --no-login
```

**Note:** This method will be removed in a future version. Migrate to Firebase authentication.

## Output Formats

Every resource listing command accepts `--format/--format json|yaml|text|table`. Table output (default) uses `rich`; JSON/YAML are convenient for scripting pipelines.

## Command Groups

| Command | Alias | Highlights |
| --- | --- | --- |
| `discovery config` | — | Initialise profiles, switch `--profile`, emit `.env` snippets, run health checks. |
| `discovery auth` | — | Manage Firebase/Google authentication: login, logout, status, refresh tokens. |
| `discovery notebooks` | `discovery nb` | CRUD operations, tag management, recent notebook tracking, blog post generation. |
| `discovery sources` | `discovery src` | Add URL/file/text sources, list or inspect sources, delete entries. |
| `discovery vectors` | `discovery vec` | Ingest notebooks, run semantic similarity queries, count/purge vectors, create collections. |
| `discovery outputs` | `discovery out` | List/create/search outputs, preview content, delete artefacts. |
| `discovery articles` | — | Fetch candidate articles for a research question. |
| `discovery qa` | — | Ask a notebook question with RAG and view service health. |

All commands respect `--profile` to target a specific configuration profile. When a notebook GUID is not supplied the CLI falls back to the last notebook you touched (`discovery notebooks recent --set <id>` to override).

## Scripting Tips

- Use `--format json` or `--format yaml` for machine-readable responses.
- Pipe results through `jq`, e.g., `discovery notebooks list --format json | jq '.notebooks[0].id'`.
- Combine with `xargs` to batch operations: `discovery sources list -n <id> --format json | jq -r '.[] | .id' | xargs -I{} discovery sources remove {}`.

## Environment Variables

- `DISCOVERY_CONFIG_HOME`: override the configuration directory (default `~/.discovery`).
- `DISCOVERY_API_URL`, `DISCOVERY_API_KEY`, `DISCOVERY_NOTEBOOK_GUID`: produced by `discovery config env` for shell integration.

## Development Notes

- Commands live under `src/cli/commands/` and share helpers (`config_store.py`, `runtime.py`, `output.py`, `utils.py`).
- Add new command groups by creating a Typer app and registering it in `src/cli/__main__.py`.
- Integration tests can mock the API using `httpx.MockTransport` or `respx`; see `tests/cli/` (create as needed).




## discovery cli examples
  
discovery --help
discovery notebooks --help
discovery config init --url http://localhost:8000
discovery notebooks list--format json
discovery src add url --notebook 380fe8dc-73ff-4b7b-a2a2-0025905a12da --format json --url https://en.wikipedia.org/wiki/Bill_Gates
discovery vectors ingest --notebook 380fe8dc-73ff-4b7b-a2a2-0025905a12da
discovery qa ask --notebook 380fe8dc-73ff-4b7b-a2a2-0025905a12da --format json --question "When was bill gates born?"
  