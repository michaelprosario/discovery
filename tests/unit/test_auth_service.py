"""Unit tests for the authentication system (entity, service, providers)."""
import pytest

from src.core.entities.user import User, ROLE_USER, ROLE_ADMIN
from src.core.services.auth_service import AuthService
from src.core.commands.auth_commands import (
    RegisterUserCommand,
    LoginCommand,
    RefreshCommand,
    LogoutCommand,
    ChangePasswordCommand,
)
from src.infrastructure.repositories.in_memory_user_repository import InMemoryUserRepository
from src.infrastructure.repositories.in_memory_refresh_token_repository import (
    InMemoryRefreshTokenRepository,
)
from src.infrastructure.providers.bcrypt_password_hasher import BcryptPasswordHasher
from src.infrastructure.providers.jwt_token_service import JwtTokenService

VALID_PASSWORD = "supersecret1"


@pytest.fixture
def hasher():
    # Low cost factor keeps the test suite fast.
    return BcryptPasswordHasher(rounds=4)


@pytest.fixture
def token_service():
    return JwtTokenService(secret_key="unit-test-secret", algorithm="HS256", access_token_expire_minutes=15)


@pytest.fixture
def service(hasher, token_service):
    return AuthService(
        user_repository=InMemoryUserRepository(),
        refresh_token_repository=InMemoryRefreshTokenRepository(),
        password_hasher=hasher,
        token_service=token_service,
        refresh_token_ttl_days=14,
    )


def _register(service, email="alice@example.com", password=VALID_PASSWORD):
    return service.register(RegisterUserCommand(email=email, password=password))


class TestUserEntity:
    def test_create_normalizes_email_and_defaults_role(self):
        result = User.create(email="  Alice@Example.COM ", password_hash="hash")
        assert result.is_success
        assert result.value.email == "alice@example.com"
        assert result.value.roles == [ROLE_USER]
        assert result.value.is_active is True

    def test_create_rejects_invalid_email(self):
        assert User.create(email="not-an-email", password_hash="hash").is_failure

    def test_validate_password_enforces_min_length(self):
        assert User.validate_password("short").is_failure
        assert User.validate_password(VALID_PASSWORD).is_success

    def test_is_admin(self):
        admin = User.create(email="a@b.com", password_hash="h", roles=[ROLE_ADMIN]).value
        assert admin.is_admin is True
        user = User.create(email="c@d.com", password_hash="h").value
        assert user.is_admin is False


class TestRegistration:
    def test_register_success(self, service):
        result = _register(service)
        assert result.is_success
        assert result.value.email == "alice@example.com"
        # password hash must not equal plaintext
        assert result.value.password_hash != VALID_PASSWORD

    def test_register_weak_password_fails(self, service):
        result = service.register(RegisterUserCommand(email="a@b.com", password="short"))
        assert result.is_failure
        assert result.validation_errors

    def test_register_duplicate_email_fails(self, service):
        _register(service)
        result = _register(service, email="Alice@example.com")  # case-insensitive dup
        assert result.is_failure
        assert result.validation_errors[0].code == "DUPLICATE_EMAIL"


class TestAuthentication:
    def test_login_success_issues_tokens(self, service, token_service):
        _register(service)
        result = service.authenticate(LoginCommand(email="alice@example.com", password=VALID_PASSWORD))
        assert result.is_success
        tokens = result.value
        assert tokens.token_type == "bearer"
        assert tokens.expires_in == 15 * 60
        claims = token_service.decode_access_token(tokens.access_token)
        assert claims.is_success
        assert claims.value["email"] == "alice@example.com"

    def test_login_wrong_password_fails(self, service):
        _register(service)
        result = service.authenticate(LoginCommand(email="alice@example.com", password="wrongpassword"))
        assert result.is_failure

    def test_login_unknown_user_fails(self, service):
        result = service.authenticate(LoginCommand(email="nobody@example.com", password=VALID_PASSWORD))
        assert result.is_failure


class TestRefreshRotation:
    def test_refresh_rotates_and_old_token_is_rejected(self, service):
        _register(service)
        tokens = service.authenticate(LoginCommand(email="alice@example.com", password=VALID_PASSWORD)).value

        rotated = service.refresh(RefreshCommand(refresh_token=tokens.refresh_token))
        assert rotated.is_success
        assert rotated.value.refresh_token != tokens.refresh_token

        # Replaying the original (now revoked) token fails — reuse detection.
        reuse = service.refresh(RefreshCommand(refresh_token=tokens.refresh_token))
        assert reuse.is_failure

    def test_reuse_revokes_entire_chain(self, service):
        _register(service)
        tokens = service.authenticate(LoginCommand(email="alice@example.com", password=VALID_PASSWORD)).value
        rotated = service.refresh(RefreshCommand(refresh_token=tokens.refresh_token)).value

        # Replay the old one -> triggers chain revocation.
        service.refresh(RefreshCommand(refresh_token=tokens.refresh_token))
        # The rotated (current) token should now also be revoked.
        assert service.refresh(RefreshCommand(refresh_token=rotated.refresh_token)).is_failure

    def test_invalid_refresh_token_fails(self, service):
        assert service.refresh(RefreshCommand(refresh_token="garbage")).is_failure


class TestLogout:
    def test_logout_revokes_refresh_token(self, service):
        _register(service)
        tokens = service.authenticate(LoginCommand(email="alice@example.com", password=VALID_PASSWORD)).value
        assert service.logout(LogoutCommand(refresh_token=tokens.refresh_token)).is_success
        assert service.refresh(RefreshCommand(refresh_token=tokens.refresh_token)).is_failure

    def test_logout_is_idempotent(self, service):
        assert service.logout(LogoutCommand(refresh_token="never-existed")).is_success


class TestChangePassword:
    def test_change_password_success_and_revokes_tokens(self, service):
        _register(service)
        tokens = service.authenticate(LoginCommand(email="alice@example.com", password=VALID_PASSWORD)).value
        result = service.change_password(ChangePasswordCommand(
            email="alice@example.com", old_password=VALID_PASSWORD, new_password="brandnew123",
        ))
        assert result.is_success
        # old refresh tokens revoked
        assert service.refresh(RefreshCommand(refresh_token=tokens.refresh_token)).is_failure
        # can log in with the new password
        assert service.authenticate(LoginCommand(email="alice@example.com", password="brandnew123")).is_success

    def test_change_password_wrong_old_fails(self, service):
        _register(service)
        result = service.change_password(ChangePasswordCommand(
            email="alice@example.com", old_password="wrongold", new_password="brandnew123",
        ))
        assert result.is_failure


class TestProviders:
    def test_bcrypt_hash_roundtrip(self, hasher):
        h = hasher.hash("a long password that exceeds bcrypt's seventy two byte input limit easily!!!")
        assert hasher.verify("a long password that exceeds bcrypt's seventy two byte input limit easily!!!", h)
        assert not hasher.verify("wrong", h)

    def test_jwt_rejects_tampered_token(self, token_service):
        token = token_service.create_access_token(__import__("uuid").uuid4(), "x@y.com", ["user"])
        assert token_service.decode_access_token(token + "tamper").is_failure

    def test_jwt_rejects_wrong_secret(self, token_service):
        token = token_service.create_access_token(__import__("uuid").uuid4(), "x@y.com", ["user"])
        other = JwtTokenService(secret_key="different-secret")
        assert other.decode_access_token(token).is_failure
