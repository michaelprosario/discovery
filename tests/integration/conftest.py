"""Shared fixtures for API integration tests.

The protected routers depend on the JWT auth dependency to resolve the current
user's email. Integration tests exercise resource CRUD, not the auth handshake,
so we override that dependency with a fixed test user (the same pattern the
tests already use for repositories).
"""
import pytest

from src.api.main import app
from src.api.auth.jwt_auth import (
    get_current_user_email,
    get_current_user_email_with_api_key,
)

TEST_USER_EMAIL = "test-user@example.com"


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "no_auth_override: do not auto-authenticate; exercise the real auth handshake",
    )


@pytest.fixture(autouse=True)
def override_auth(request):
    """Authenticate every integration request as a fixed test user.

    Tests marked ``no_auth_override`` opt out (e.g. the auth-router tests that
    verify the real token handshake).
    """
    if request.node.get_closest_marker("no_auth_override"):
        yield
        return

    async def _fixed_user() -> str:
        return TEST_USER_EMAIL

    app.dependency_overrides[get_current_user_email] = _fixed_user
    app.dependency_overrides[get_current_user_email_with_api_key] = _fixed_user
    yield
    app.dependency_overrides.pop(get_current_user_email, None)
    app.dependency_overrides.pop(get_current_user_email_with_api_key, None)
