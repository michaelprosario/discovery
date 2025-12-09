- Make a specifiction for adding a static api key to authenticate all major fast api actions.
- authentication should attempt to user firebase auth first.
- alternatively, use api key authentication
- static api key should be defined by environment variable

===

# Plan: Add Static API Key Authentication to FastAPI

Add dual authentication supporting Firebase ID tokens (primary) and static API key (fallback) for all major FastAPI endpoints. Firebase auth attempts first; if missing or invalid, static API key from environment variable is checked. This ensures backward compatibility while enabling simpler API key access.

## Steps

1. **Create dual authentication dependency** in `src/application/auth/authentication.py` that tries Firebase token via `get_current_user_email()`, falls back to validating `X-API-Key` header against `STATIC_API_KEY` env var, returns system user email (e.g., `api_key_user@system`) for API key auth

2. **Add `STATIC_API_KEY` environment variable** to `.env.template` and update `DEPLOYMENT_GUIDE.md` with secure key generation instructions (e.g., using `secrets.token_urlsafe(32)`)

3. **Apply new dual auth dependency** to unauthenticated major endpoints in `src/interfaces/api/routers/vector_search_router.py` (5 endpoints), `qa_router.py` (1 endpoint), `mindmap_router.py` (2 endpoints), `article_search_router.py` (1 endpoint), and 6 unauthenticated endpoints in `sources_router.py`

4. **Update authenticated endpoints** in `notebooks_router.py` (9 endpoints), `outputs_router.py` (7 endpoints), and 4 authenticated `sources_router.py` endpoints to use new dual auth dependency instead of `get_current_user_email()`

5. **Handle system user authorization** by modifying resource ownership checks (`require_resource_owner_or_fail`, `check_resource_exists_and_owner`) to allow API key system user to bypass ownership validation or access all resources


## Further Considerations

1. **System user authorization scope** 
- API key have full access to all resources (Option A: admin-like)


3. **Optional vs required** - Keep health/root endpoints public
