"""HTTP-level integration tests for the auth router (register/token/refresh/me).

Uses dependency overrides to bind the AuthService to in-memory repositories so
the flow runs without a database, while still exercising the real router,
OAuth2 form parsing, JWT issuance and bearer verification.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from src.api.main import app
from src.api.dependencies.auth import get_auth_service, get_token_service
from src.core.services.auth_service import AuthService
from src.infrastructure.repositories.in_memory_user_repository import InMemoryUserRepository
from src.infrastructure.repositories.in_memory_refresh_token_repository import (
    InMemoryRefreshTokenRepository,
)
from src.infrastructure.providers.bcrypt_password_hasher import BcryptPasswordHasher
from src.infrastructure.providers.jwt_token_service import JwtTokenService

PASSWORD = "supersecret1"

# These tests drive the real token handshake — opt out of the conftest
# auto-authentication so bearer verification actually runs.
pytestmark = pytest.mark.no_auth_override


@pytest.fixture(autouse=True)
def override_auth_service():
    """Bind a single in-memory AuthService for the whole test (shared state)."""
    users = InMemoryUserRepository()
    tokens = InMemoryRefreshTokenRepository()
    hasher = BcryptPasswordHasher(rounds=4)
    token_service = JwtTokenService(secret_key="integration-secret", access_token_expire_minutes=15)
    service = AuthService(users, tokens, hasher, token_service, refresh_token_ttl_days=14)

    app.dependency_overrides[get_auth_service] = lambda: service
    app.dependency_overrides[get_token_service] = lambda: token_service
    yield
    app.dependency_overrides.pop(get_auth_service, None)
    app.dependency_overrides.pop(get_token_service, None)


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_register_login_me_and_refresh(client):
    async with client:
        # Register
        r = await client.post("/api/auth/register", json={"email": "Bob@Example.com", "password": PASSWORD})
        assert r.status_code == 201, r.text
        assert r.json()["email"] == "bob@example.com"

        # Token (OAuth2 password grant — form encoded)
        r = await client.post("/api/auth/token", data={"username": "bob@example.com", "password": PASSWORD})
        assert r.status_code == 200, r.text
        body = r.json()
        access, refresh = body["access_token"], body["refresh_token"]
        assert body["token_type"] == "bearer"

        # /me with bearer token
        r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {access}"})
        assert r.status_code == 200
        assert r.json()["email"] == "bob@example.com"

        # Refresh rotates the token
        r = await client.post("/api/auth/refresh", json={"refresh_token": refresh})
        assert r.status_code == 200
        assert r.json()["access_token"]

        # Old refresh token is now rejected (rotation + reuse detection)
        r = await client.post("/api/auth/refresh", json={"refresh_token": refresh})
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_requires_token(client):
    async with client:
        # No token -> 401
        r = await client.get("/api/auth/me")
        assert r.status_code == 401
        # Bad token -> 401
        r = await client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client):
    async with client:
        await client.post("/api/auth/register", json={"email": "carol@example.com", "password": PASSWORD})
        r = await client.post("/api/auth/token", data={"username": "carol@example.com", "password": "wrongpass1"})
        assert r.status_code == 401
