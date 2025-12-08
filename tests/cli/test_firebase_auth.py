"""Tests for Firebase authentication."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.cli.config_store import FirebaseCredentials
from src.cli.exceptions import DiscoveryCLIError
from src.cli.firebase_client import FirebaseAuthClient


@pytest.fixture
def mock_firebase_credentials():
    """Create mock Firebase credentials."""
    return FirebaseCredentials(
        id_token="mock_id_token_12345",
        refresh_token="mock_refresh_token_67890",
        token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
        user_email="test@example.com",
    )


@pytest.fixture
def expired_firebase_credentials():
    """Create expired Firebase credentials."""
    return FirebaseCredentials(
        id_token="mock_id_token_expired",
        refresh_token="mock_refresh_token_67890",
        token_expiry=datetime.now(timezone.utc) - timedelta(hours=1),
        user_email="test@example.com",
    )


class TestFirebaseAuthClient:
    """Test FirebaseAuthClient functionality."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        client = FirebaseAuthClient(api_key="test_api_key")
        assert client.api_key == "test_api_key"

    def test_init_without_api_key_raises_error(self):
        """Test initialization without API key raises error."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(DiscoveryCLIError, match="Firebase Web API key not configured"):
                FirebaseAuthClient()

    def test_init_with_env_var(self):
        """Test initialization with environment variable."""
        with patch.dict("os.environ", {"FIREBASE_WEB_API_KEY": "env_api_key"}):
            client = FirebaseAuthClient()
            assert client.api_key == "env_api_key"

    @patch("src.cli.firebase_client.requests.post")
    def test_refresh_token_success(self, mock_post, mock_firebase_credentials):
        """Test successful token refresh."""
        # Mock the refresh response
        mock_response = Mock()
        mock_response.json.return_value = {
            "id_token": "new_id_token",
            "refresh_token": "new_refresh_token",
            "expires_in": "3600",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = FirebaseAuthClient(api_key="test_key")
        new_creds = client.refresh_token(mock_firebase_credentials)

        assert new_creds.id_token == "new_id_token"
        assert new_creds.refresh_token == "new_refresh_token"
        assert new_creds.user_email == "test@example.com"
        assert new_creds.token_expiry > datetime.now(timezone.utc)

    @patch("src.cli.firebase_client.requests.post")
    def test_refresh_token_failure(self, mock_post, mock_firebase_credentials):
        """Test token refresh failure."""
        mock_post.side_effect = Exception("Network error")

        client = FirebaseAuthClient(api_key="test_key")
        with pytest.raises(DiscoveryCLIError, match="Failed to refresh Firebase token"):
            client.refresh_token(mock_firebase_credentials)

    def test_get_valid_token_with_valid_token(self, mock_firebase_credentials):
        """Test getting valid token when token is not expired."""
        client = FirebaseAuthClient(api_key="test_key")
        token = client.get_valid_token(mock_firebase_credentials)
        assert token == "mock_id_token_12345"

    @patch("src.cli.firebase_client.requests.post")
    def test_get_valid_token_refreshes_expired(self, mock_post, expired_firebase_credentials):
        """Test getting valid token refreshes when expired."""
        # Mock the refresh response
        mock_response = Mock()
        mock_response.json.return_value = {
            "id_token": "refreshed_id_token",
            "refresh_token": "refreshed_refresh_token",
            "expires_in": "3600",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = FirebaseAuthClient(api_key="test_key")
        token = client.get_valid_token(expired_firebase_credentials)
        
        assert token == "refreshed_id_token"
        assert mock_post.called

    def test_get_oauth_client_config_missing_credentials(self):
        """Test OAuth config fails without credentials."""
        with patch.dict("os.environ", {"FIREBASE_WEB_API_KEY": "test_key"}, clear=True):
            client = FirebaseAuthClient(api_key="test_key")
            with pytest.raises(DiscoveryCLIError, match="Google OAuth credentials not configured"):
                client._get_oauth_client_config()

    def test_get_oauth_client_config_success(self):
        """Test OAuth config with valid credentials."""
        with patch.dict(
            "os.environ",
            {
                "FIREBASE_WEB_API_KEY": "test_key",
                "GOOGLE_OAUTH_CLIENT_ID": "test_client_id",
                "GOOGLE_OAUTH_CLIENT_SECRET": "test_client_secret",
            },
        ):
            client = FirebaseAuthClient(api_key="test_key")
            config = client._get_oauth_client_config()
            
            assert "installed" in config
            assert config["installed"]["client_id"] == "test_client_id"
            assert config["installed"]["client_secret"] == "test_client_secret"

    @patch("src.cli.firebase_client.InstalledAppFlow.from_client_config")
    @patch("src.cli.firebase_client.requests.post")
    def test_login_local_redirect_flow(self, mock_post, mock_flow_class):
        """Test login with local redirect flow."""
        # Mock OAuth flow
        mock_flow = Mock()
        mock_credentials = Mock()
        mock_credentials.id_token = "google_id_token"
        mock_credentials.token = {"email": "test@example.com"}
        mock_flow.run_local_server.return_value = mock_credentials
        mock_flow_class.return_value = mock_flow

        # Mock Firebase token exchange
        mock_response = Mock()
        mock_response.json.return_value = {
            "idToken": "firebase_id_token",
            "refreshToken": "firebase_refresh_token",
            "expiresIn": "3600",
            "email": "test@example.com",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        with patch.dict(
            "os.environ",
            {
                "FIREBASE_WEB_API_KEY": "test_key",
                "GOOGLE_OAUTH_CLIENT_ID": "test_client_id",
                "GOOGLE_OAUTH_CLIENT_SECRET": "test_client_secret",
            },
        ):
            client = FirebaseAuthClient(api_key="test_key")
            creds = client.login(use_device_flow=False)

            assert creds.id_token == "firebase_id_token"
            assert creds.refresh_token == "firebase_refresh_token"
            assert creds.user_email == "test@example.com"
            assert mock_flow.run_local_server.called


class TestFirebaseCredentials:
    """Test FirebaseCredentials model."""

    def test_create_credentials(self):
        """Test creating Firebase credentials."""
        expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        creds = FirebaseCredentials(
            id_token="test_token",
            refresh_token="test_refresh",
            token_expiry=expiry,
            user_email="test@example.com",
        )

        assert creds.id_token == "test_token"
        assert creds.refresh_token == "test_refresh"
        assert creds.token_expiry == expiry
        assert creds.user_email == "test@example.com"

    def test_credentials_serialization(self):
        """Test credentials can be serialized."""
        expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        creds = FirebaseCredentials(
            id_token="test_token",
            refresh_token="test_refresh",
            token_expiry=expiry,
            user_email="test@example.com",
        )

        # Should be able to serialize to dict
        data = creds.model_dump()
        assert data["id_token"] == "test_token"
        assert data["user_email"] == "test@example.com"

        # Should be able to reconstruct
        new_creds = FirebaseCredentials.model_validate(data)
        assert new_creds.id_token == creds.id_token
        assert new_creds.user_email == creds.user_email
