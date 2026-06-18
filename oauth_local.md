# Proposal: Internal Registration & Auth System (OAuth2 + JWT)

**Branch:** `feat/edits-for-local-usage`
**Status:** Proposal / design — no code written yet.
**Companion doc:** [`removeFirebaseAuth.md`](./removeFirebaseAuth.md). This proposal is the
*sequel*: that doc strips Firebase and leaves a single fixed `LOCAL_USER_EMAIL`; this doc
replaces that stub with a real, self-contained auth provider owned by the backend.

---

## 1. Goal & scope

Add a **first-party authentication system** to the FastAPI backend so users can register
and log in without any external identity provider. It must:

- Use **OAuth2 patterns** (token endpoint, bearer tokens, scopes/roles).
- Issue and verify **JWT** access tokens, with **refresh tokens** for session longevity.
- Slot into the existing **Clean Architecture** (core / infrastructure / api) and the
  **`Result`** pattern, mirroring how notebooks/sources/outputs are built.
- Preserve the existing `created_by` (email) ownership model so **no router business logic
  or DB schema for existing tables changes** — the auth dependency keeps returning an
  email string, it's just now backed by a verified internal JWT instead of Firebase.

Out of scope: social login, multi-tenant orgs, MFA (noted as future work in §11).

---

## 2. Which OAuth2 flow?

OAuth2 defines several grant types. For a **first-party app** (the same team owns the
frontend, backend, and CLI), the **Resource Owner Password Credentials grant** is the
right fit and is the flow FastAPI supports natively via `OAuth2PasswordBearer` +
`OAuth2PasswordRequestForm`:

| Flow | Fit here | Verdict |
|------|----------|---------|
| **Password grant** (user posts username+password to `/token`, gets JWT) | First-party SPA + CLI; no third-party clients | ✅ **Recommended** |
| Authorization Code + PKCE | Needed when third parties get delegated access via a consent screen | ❌ Overkill for a single first-party app; revisit only if exposing the API to external clients |
| Client Credentials | Machine-to-machine, no user | ➖ Optional later for service/API keys (see §10) |

We adopt **password grant + refresh tokens with rotation**. This gives the OAuth2 surface
(`/token`, `Authorization: Bearer`, scopes) without the complexity of a full auth-code
server.

---

## 3. Token design

Two token types, both JWT, signed **HS256** with a server secret (`JWT_SECRET_KEY`).

> RS256 (asymmetric keypair) is an alternative if we ever want other services to *verify*
> tokens without holding the signing secret. For a single self-contained backend, HS256 is
> simpler and sufficient. The algorithm is config-driven so this can change without code
> edits.

### Access token (short-lived, ~15 min)
Sent on every request as `Authorization: Bearer <jwt>`. Stateless — never hits the DB on
verification.

```jsonc
{
  "sub": "<user_uuid>",       // subject = user id
  "email": "user@example.com",
  "roles": ["user"],          // becomes OAuth2 "scopes"
  "type": "access",
  "iat": 1718600000,
  "exp": 1718600900,
  "jti": "<uuid>"             // unique id, enables future blocklisting
}
```

### Refresh token (long-lived, ~14 days)
Used only at `POST /api/auth/refresh` to mint a new access token. **Stored hashed in the
DB** so it can be revoked (logout) and **rotated** (each refresh issues a new refresh token
and invalidates the old one). Reuse of an already-rotated token → revoke the whole chain
(reuse-detection), a standard refresh-rotation safeguard.

This hybrid keeps access verification stateless/fast while still allowing real logout and
revocation through the refresh table.

---

## 4. Architecture mapping (Clean Architecture)

New code follows the exact layering already used for `Notebook`:

```
src/
├── core/
│   ├── entities/
│   │   └── user.py                         # User dataclass + create()/verify, Result-based validation
│   ├── commands/
│   │   └── auth_commands.py                 # RegisterUserCommand, LoginCommand, RefreshCommand, ...
│   ├── queries/
│   │   └── user_queries.py                  # GetUserByEmailQuery, GetUserByIdQuery
│   ├── interfaces/
│   │   ├── repositories/
│   │   │   ├── i_user_repository.py         # IUserRepository
│   │   │   └── i_refresh_token_repository.py# IRefreshTokenRepository
│   │   └── providers/
│   │       ├── i_password_hasher.py         # hash() / verify()
│   │       └── i_token_service.py           # issue/decode JWTs
│   └── services/
│       └── auth_service.py                  # register / authenticate / refresh / logout → Result[...]
├── infrastructure/
│   ├── database/
│   │   └── models.py                        # + UserModel, RefreshTokenModel
│   ├── repositories/
│   │   ├── postgres_user_repository.py
│   │   └── postgres_refresh_token_repository.py
│   ├── providers/
│   │   ├── pwdlib_password_hasher.py        # argon2/bcrypt impl of IPasswordHasher
│   │   └── jwt_token_service.py             # PyJWT impl of ITokenService
│   └── migrations/versions/
│       └── xxxx_add_users_and_refresh_tokens.py
└── api/
    ├── auth/
    │   ├── jwt_auth.py                       # REPLACES firebase_auth.py: OAuth2PasswordBearer + get_current_user
    │   └── authorization.py                  # KEPT from removeFirebaseAuth.md (role/owner checks)
    ├── auth_router.py                        # /api/auth/* endpoints
    ├── dependencies/auth.py                  # DI wiring for AuthService, hasher, token service
    └── dtos.py                               # + RegisterRequest, TokenResponse, UserResponse, ...
```

Domain layer stays pure: hashing and JWT signing are **interfaces in core**, implemented in
**infrastructure** (Dependency Inversion, exactly like `IArticleSearchProvider`). The
`AuthService` returns `Result[...]` and never raises for business failures (duplicate
email, bad credentials), matching the rest of the codebase.

---

## 5. Data model

### `User` entity (`core/entities/user.py`)
Dataclass with a `create()` factory that validates via `ValidationError`/`Result`, mirroring
`Notebook.create()`:

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | `uuid4` default |
| `email` | `str` | unique, lowercased, validated (`@`) — this is the value used as `created_by` everywhere |
| `password_hash` | `str` | never the plaintext; entity exposes no getter that leaks it |
| `display_name` | `Optional[str]` | |
| `roles` | `List[str]` | default `["user"]`; `"admin"` replaces the old `SYSTEM_USER_EMAIL` "see-all" bypass |
| `is_active` | `bool` | default `True`; soft-disable without delete |
| `created_at` / `updated_at` | `datetime` | utc |

Validation rules in `create()`: valid email, password policy (min length ≥ 8, etc.),
display name length. Plaintext password is hashed in the **service** (which holds the
`IPasswordHasher`), not in the entity, to keep the entity infrastructure-free.

### SQLAlchemy models (`infrastructure/database/models.py`)
- `UserModel` → `users` table: `id (PG_UUID pk)`, `email (String unique, index)`,
  `password_hash (String)`, `display_name (String null)`, `roles (JSONEncodedList)`,
  `is_active (Boolean)`, `created_at`, `updated_at`. Reuses the existing `JSONEncodedList`
  type decorator for cross-DB (Postgres/SQLite) compatibility.
- `RefreshTokenModel` → `refresh_tokens` table: `id (PG_UUID pk)`,
  `user_id (FK users.id, CASCADE, index)`, `token_hash (String, index)`,
  `expires_at (DateTime)`, `revoked_at (DateTime null)`, `created_at`. Store only a hash of
  the refresh token, never the raw value.

### Migration
New Alembic revision `add_users_and_refresh_tokens` creating both tables. **Existing
tables are untouched** — `created_by` columns already exist (from
`add_created_by_to_all_tables`). A small data step seeds a default user for any rows
previously created under the transitional `local@discovery.local` (see §8).

---

## 6. Endpoints (`api/auth_router.py`, prefix `/api/auth`)

| Method | Path | Body | Returns | Notes |
|--------|------|------|---------|-------|
| `POST` | `/register` | `RegisterRequest{email, password, display_name?}` | `UserResponse` | 409 on duplicate email; gated by `ALLOW_REGISTRATION` flag (§9) |
| `POST` | `/token` | `OAuth2PasswordRequestForm` (`username`, `password`) | `TokenResponse{access_token, refresh_token, token_type, expires_in}` | The OAuth2 token endpoint; `username` = email |
| `POST` | `/refresh` | `{refresh_token}` | `TokenResponse` | Rotates refresh token; reuse-detection revokes chain |
| `POST` | `/logout` | `{refresh_token}` | `204` | Marks refresh token revoked |
| `GET` | `/me` | — (Bearer) | `UserResponse` | Current authenticated user |
| `POST` | `/change-password` | `{old_password, new_password}` (Bearer) | `204` | Optional, phase 2 |

All DTOs added to `api/dtos.py` next to the existing request/response models. Validation
errors surface through the same `ValidationErrorResponse` shape already used by other
routers.

---

## 7. The auth dependency (continuity with `removeFirebaseAuth.md`)

`removeFirebaseAuth.md` replaced Firebase with stub dependencies that return a constant.
This proposal swaps the stub for a real JWT verifier **with the same public names and
return type**, so the ~35 endpoints across the 7 routers stay byte-for-byte unchanged:

```python
# api/auth/jwt_auth.py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token", auto_error=True)

async def get_current_user(token: str = Depends(oauth2_scheme),
                           token_service: ITokenService = Depends(get_token_service)) -> User:
    payload = token_service.decode_access(token)          # raises 401 on invalid/expired
    # ... load/validate user, ensure is_active ...
    return user

async def get_current_user_email(user: User = Depends(get_current_user)) -> str:
    return user.email                                      # <-- routers already depend on this name

# Back-compat alias so existing `Depends(get_current_user_email_with_api_key)` keeps working:
get_current_user_email_with_api_key = get_current_user_email
```

Because routers consume `current_user_email: str = Depends(get_current_user_email_with_api_key)`,
**only this one file changes**; the routers do not. The `SYSTEM_USER_EMAIL` "see-all"
branch (`notebooks_router.py:331`) is reframed as a **role check** — replace the
`== SYSTEM_USER_EMAIL` comparison with "does the current user have the `admin` role"
(a tiny, optional follow-up; the email-based path keeps working until then).

`api/auth/authorization.py` (`require_resource_owner_or_fail`) is reused as-is.

---

## 8. Migration & rollout from the `removeFirebaseAuth` state

1. Land `removeFirebaseAuth.md` first (no external auth, single local user).
2. Add the users/refresh tables migration.
3. Seed one user (env-driven `BOOTSTRAP_ADMIN_EMAIL` / `BOOTSTRAP_ADMIN_PASSWORD`, or a
   `discovery auth register` CLI call) and **reassign** any rows whose
   `created_by == "local@discovery.local"` to that user's email — a one-line `UPDATE` per
   table inside the migration's data step (or a standalone script under `scripts/`).
4. Flip the auth dependency from stub to `jwt_auth`. Existing data now belongs to a real
   account; everything else is unchanged.

This keeps the transition reversible and avoids a flag-day rewrite.

---

## 9. Configuration (env vars → `.env.example`)

```bash
# --- Internal Auth (OAuth2 + JWT) ---
JWT_SECRET_KEY=                 # REQUIRED. Generate: python -c "import secrets; print(secrets.token_urlsafe(48))"
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=14
ALLOW_REGISTRATION=true         # set false to lock down open sign-up (invite/admin-only)
# Optional one-time bootstrap admin
BOOTSTRAP_ADMIN_EMAIL=
BOOTSTRAP_ADMIN_PASSWORD=
```

The app should **refuse to start (or loudly warn) if `JWT_SECRET_KEY` is unset** — never
fall back to a hardcoded default secret.

---

## 10. Dependencies (`pyproject.toml`)

Add as **direct** deps (note: `pyjwt` and `bcrypt` currently appear in `uv.lock` only as
transitive deps of `firebase-admin`, so they'll disappear when that's removed — they must
be declared explicitly):

- `pyjwt>=2.8.0` — JWT encode/decode (maintained; preferred over the less-active
  `python-jose`).
- `pwdlib[argon2]>=0.2.0` — modern password hashing recommended by FastAPI; Argon2id by
  default. *Alternative:* `passlib[bcrypt]` if the team prefers the established library.
- `python-multipart>=0.0.9` — **required** by FastAPI to parse `OAuth2PasswordRequestForm`
  (form-encoded `/token` body).

Keep `google-auth*` (used by Gemini providers, unrelated to auth).

---

## 11. Security considerations

- **Hashing:** Argon2id (or bcrypt) with sane cost; never store or log plaintext.
- **Refresh rotation + reuse detection:** every refresh rotates; a replayed old token
  revokes the whole chain.
- **Secret management:** `JWT_SECRET_KEY` from env only; rotating it invalidates all live
  tokens (acceptable, documented). RS256 available if multi-service verification is needed.
- **Rate limiting / lockout:** throttle `/token` and `/register` (e.g. SlowAPI middleware)
  and consider temporary lockout after N failed logins to blunt brute force.
- **CORS:** `main.py` currently uses `allow_origins=["*"]` with `allow_credentials=True`.
  Tighten to known origins once auth is real (Bearer tokens make wildcard origins less
  catastrophic, but it should still be scoped).
- **Token storage (frontend):** prefer in-memory access token + refresh handled carefully;
  document XSS/CSRF trade-offs for the Angular client.
- **Generic auth errors:** return "invalid credentials" without revealing whether the email
  exists.
- **Future:** email verification, password reset flow, MFA/TOTP, admin user management,
  audit log — all additive on this foundation.

---

## 12. CLI integration

The existing `src/cli/commands/auth.py` already stores a credential in the profile and the
HTTP client sends it. Adapt it to the new flow:

- `discovery auth register --email ... ` → `POST /api/auth/register`.
- `discovery auth login --email ... ` → `POST /api/auth/token`; persist `access_token` +
  `refresh_token` in the profile (replacing the static `api_key` field).
- `http_client` sends `Authorization: Bearer <access_token>`; on 401, transparently call
  `/refresh` once and retry.
- `discovery auth logout` → `POST /api/auth/logout` then clear stored tokens.
- `discovery auth status` → decode/show the current user + token expiry.

*(Optional)* a **Client Credentials**-style long-lived API key for headless/CI use can be
layered on later as a separate grant without touching the user/password path.

---

## 13. Testing plan

- **Entity unit tests** (`tests/`): `User.create()` validation (email, password policy),
  role defaults — mirrors existing notebook entity tests.
- **Service tests** with in-memory user/refresh repos (pattern already exists:
  `in_memory_*_repository.py`): register duplicate → failure `Result`; authenticate
  good/bad password; refresh rotation; reuse detection; logout revocation.
- **Provider tests:** hasher round-trip; token service issue→decode, expiry, tampered
  signature rejected.
- **API/integration tests:** register → token → call a protected notebook endpoint with the
  Bearer token → 200; missing/expired token → 401; refresh → new access token works;
  ownership isolation between two users.

---

## 14. Phased roadmap

1. **Phase 0** — land `removeFirebaseAuth.md` (clean slate, single local user).
2. **Phase 1** — core: `User` entity, interfaces, `AuthService`; infra: models + migration,
   Postgres + in-memory repos, hasher + JWT providers. Unit-tested in isolation.
3. **Phase 2** — api: `auth_router` (`/register`, `/token`, `/refresh`, `/logout`, `/me`),
   DTOs, DI wiring; swap the auth dependency to `jwt_auth`; data-migrate existing rows.
4. **Phase 3** — role-based "see-all" (replace `SYSTEM_USER_EMAIL` branch with `admin`
   role), CLI integration, CORS tightening, rate limiting.
5. **Phase 4** *(optional)* — password reset / email verification / API keys / MFA.

---

## Summary

A first-party **OAuth2 password-grant + JWT** system that drops cleanly into the existing
Clean Architecture: a `User` entity and `AuthService` returning `Result`, JWT/hashing behind
core interfaces, two new tables via Alembic, and an `/api/auth/*` router. The crucial design
choice — **the auth dependency keeps returning the user's email string** — means every
existing router and the `created_by` ownership model continue to work unchanged; we are
swapping *where the email comes from* (a verified internal JWT) rather than rewiring the app.
