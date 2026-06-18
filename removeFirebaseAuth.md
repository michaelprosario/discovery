# Removing Firebase Authentication from the Backend (`src/`)

**Branch:** `feat/edits-for-local-usage`
**Goal:** Strip all Firebase authentication code from the Python backend so the app runs
without any auth provider configured, while keeping the data model (per-record
`created_by` ownership) intact. This document is the change plan — no code is modified yet.

---

## 1. Current state

Authentication lives in `src/api/auth/` and is wired into every router via FastAPI
`Depends(...)`.

### Files
| File | Role |
|------|------|
| `src/api/auth/firebase_auth.py` | Firebase Admin SDK init + token verification + dual (token / API-key) dependencies. **Firebase-specific — to be removed/replaced.** |
| `src/api/auth/authorization.py` | `require_resource_owner*` ownership checks. **Not Firebase-specific — keep.** |
| `src/api/auth/__init__.py` | Empty package marker. Keep. |

### What `firebase_auth.py` provides
- `initialize_firebase()` — lazy Firebase Admin SDK init from `FIREBASE_CREDENTIALS_PATH`
  or `FIREBASE_SERVICE_ACCOUNT_JSON`.
- `get_current_user_email()` — verifies a Firebase ID token (Bearer), returns the email. (imported by `notebooks_router`, `sources_router`, `outputs_router` but **not actually used** in any `Depends` — see §4.)
- `get_optional_user_email()` — optional variant, returns `None` if no/invalid token. **Not used anywhere.**
- `get_current_user_email_with_api_key()` — **the dependency actually used by every router.**
  Tries Firebase token first, then falls back to `STATIC_API_KEY` (returning
  `SYSTEM_USER_EMAIL = "api_key_user@system"`). Raises 401 if both fail.
- `SYSTEM_USER_EMAIL` constant (also defined in `authorization.py`).

### Where it's consumed (the dependency that matters)
`get_current_user_email_with_api_key` is injected as `current_user_email` into endpoints in:
- `src/api/notebooks_router.py` (9 endpoints + special `SYSTEM_USER_EMAIL` branch at line ~331)
- `src/api/sources_router.py` (11 endpoints)
- `src/api/outputs_router.py` (6 endpoints)
- `src/api/vector_search_router.py` (5 endpoints)
- `src/api/qa_router.py` (1 endpoint)
- `src/api/mindmap_router.py` (2 endpoints)
- `src/api/article_search_router.py` (1 endpoint)

`current_user_email` is used two ways:
1. Passed as `created_by` when creating notebooks/sources/outputs.
2. Passed to `require_resource_owner_or_fail(...)` and to per-user list filters
   (e.g. `notebooks_router.py:331`, where `SYSTEM_USER_EMAIL` sees *all* records).

### Other touch points
- `pyproject.toml:29` — `"firebase-admin>=6.0.0"` dependency.
- `uv.lock` — transitive Firebase packages.
- `.env.example:29-38` — `FIREBASE_CREDENTIALS_PATH`, `FIREBASE_SERVICE_ACCOUNT_JSON`,
  `STATIC_API_KEY`.
- `tests/` — **no references** to Firebase or the auth dependencies (verified via grep). No test changes required.
- CLI (`src/cli/commands/auth.py`) — only manages a static API-key in the local config
  profile and sends it to the backend; it never touches Firebase. Out of scope but see §6.

---

## 2. Design decision — replace, don't rip out

The cleanest low-risk change for local usage is to **keep the dependency *names and
signatures* but make them return a fixed local user**, rather than deleting the
`Depends(...)` from ~35 endpoints and rewriting every command construction.

Rationale:
- `created_by` ownership is part of the data model and DB schema (`add_created_by_to_all_tables`
  migration). Removing it entirely is a much larger, riskier change.
- Keeping the dependency seam means routers are untouched; if real auth is ever
  reintroduced, only one file changes.
- For a single-user local app, "one fixed owner who owns everything" is the correct
  semantic.

### The approach
Replace `src/api/auth/firebase_auth.py` with a small `local_auth.py` (or rewrite the same
file) that exposes the **same public names** the routers import, but with no Firebase:

```python
"""Local (no-auth) user resolution for FastAPI. Replaces Firebase auth for local usage."""

# Single local user that owns all resources.
LOCAL_USER_EMAIL = "local@discovery.local"
# Kept for backward-compat with authorization.py / notebooks_router filter logic.
SYSTEM_USER_EMAIL = LOCAL_USER_EMAIL


async def get_current_user_email() -> str:
    return LOCAL_USER_EMAIL


async def get_current_user_email_with_api_key() -> str:
    return LOCAL_USER_EMAIL
```

Key detail: set `SYSTEM_USER_EMAIL == LOCAL_USER_EMAIL`. Then the existing
"system user sees all notebooks" branch (`notebooks_router.py:331`) and the
`require_resource_owner*` bypass in `authorization.py` automatically grant the local user
full access to everything — no router edits needed, and ownership filters become no-ops.

---

## 3. Change plan (file by file)

### `src/api/auth/firebase_auth.py`
- **Action:** Replace entire contents with the no-auth implementation above
  (or delete and create `local_auth.py` + update the 7 router imports).
- **Recommendation:** rewrite the file in place and keep the filename's *imports* working
  by re-exporting from a new `local_auth.py`. Simplest is to just rewrite
  `firebase_auth.py` itself (rename later if desired) so router import lines stay valid.
- Remove: `initialize_firebase`, `get_optional_user_email`, all `firebase_admin` imports,
  `HTTPBearer`/`HTTPAuthorizationCredentials`/`Header` machinery, `os`/`json`/`lru_cache`
  imports that are no longer needed.

### `src/api/auth/authorization.py`
- **Action:** Keep. Optionally update `SYSTEM_USER_EMAIL` here to import from the new
  module so there's a single source of truth (currently duplicated). The ownership-bypass
  logic continues to work unchanged.

### Routers (`notebooks_router.py`, `sources_router.py`, `outputs_router.py`,
`vector_search_router.py`, `qa_router.py`, `mindmap_router.py`, `article_search_router.py`)
- **Action:** No functional changes required if names are preserved.
- The `from .auth.firebase_auth import ...` lines keep working (or update the module path
  if renamed to `local_auth`).
- `SYSTEM_USER_EMAIL` import in `notebooks_router.py` still resolves; the filter at
  line ~331 now always takes the "see all" branch for the local user. Optionally simplify
  that branch to just `notebooks = result.value`.

### `pyproject.toml`
- **Action:** Remove line 29 `"firebase-admin>=6.0.0"`.
- Then run `uv lock` to regenerate `uv.lock` (drops `firebase-admin`, `google-cloud-*`,
  `cachecontrol`, `pyjwt`, etc. that came in only for Firebase). Verify nothing else
  depends on them — `google-genai`, `google-auth`, `google-auth-oauthlib` stay (used by
  Gemini providers).

### `.env.example`
- **Action:** Delete the "Firebase Authentication Configuration" block and the
  `STATIC_API_KEY` block (lines 29-38). Optionally also clean the same vars from `.env`.

### `Dockerfile` / `DOCKER.md` / `README.md`
- **Action:** Grep for Firebase/auth setup instructions and `STATIC_API_KEY` / `FIREBASE_*`
  env references; remove or mark as not-required for local usage. (Documentation cleanup —
  verify with `grep -ri firebase README.md DOCKER.md Dockerfile docker-compose.yml`.)

---

## 4. Notes / gotchas

- `get_current_user_email` (token-only, no API-key fallback) is **imported** by three
  routers but is **never** placed in a `Depends(...)` — only `get_current_user_email_with_api_key`
  is. Keeping a no-op version of both avoids breaking the imports.
- `get_optional_user_email` has zero usages and can be dropped.
- The HTTP layer currently returns 401 when unauthenticated. After this change every
  request is "authenticated" as the local user, so endpoints documenting `401` responses
  will never emit them. The `401` response models in router decorators are harmless but
  could be cleaned up later.
- `openapi.json` (committed) will be stale re: the removed Bearer/API-key security schemes.
  Regenerate if it's used for client generation.

---

## 5. Verification checklist

After the change:
1. `uv sync` — confirms `firebase-admin` is gone and the env still resolves.
2. `grep -rni firebase src/` — should return **nothing**.
3. Start the API (`uvicorn src.api.main:app`) — no Firebase init warnings; `/health` 200.
4. Exercise create + list + get + delete for a notebook with **no** Authorization header
   and **no** `X-API-Key` — all should succeed and records carry
   `created_by = "local@discovery.local"`.
5. `pytest` — confirm the suite still passes (no auth references in tests today).

---

## 6. Out of scope (related, not part of "src backend")

These also contain Firebase but were **not** requested in this task. Flagging so they
aren't forgotten — the frontend will still try to authenticate against a backend that no
longer checks tokens, which works (token is simply ignored) but should be cleaned up
separately:

- **Angular frontend** `discoveryPortal/`:
  `app.config.ts`, `app.module.ts`, `core/services/auth.service.ts`,
  `core/interceptors/auth.interceptor.ts`, `environments/*.ts`, and `@angular/fire` /
  `firebase` npm deps.
- **CLI** `src/cli/commands/auth.py`: manages a static API key in the local profile.
  Now that the backend ignores auth, this becomes a no-op but does no harm; can be
  simplified/removed in a follow-up.
