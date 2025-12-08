"""Tests for Firebase email/password authentication."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest
import requests

from src.cli.config_store import FirebaseCredentials
from src.cli.exceptions import DiscoveryCLIError
from src.cli.firebase_email_auth import FirebaseEmailAuthClient


@pytest.fixture
def firebase_email_client():
    """Create Firebase email auth client."""
    return FirebaseEmailAuthClient(api_key="test_api_key")


class TestFirebaseEmailAuthClient:
    """Test FirebaseEmailAuthClient functionality."""

    def test_init(self):
        """Test initialization."""
        client = FirebaseEmailAuthClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert "identitytoolkit.googleapis.com" in client.base_url

    @patch("src.cli.firebase_email_auth.requests.post")
    def test_sign_in_with_email_password_success(self, mock_post, firebase_email_client):
        """Test successful email/password sign in."""
        # Mock the sign-in response
        mock_response = Mock()
        mock_response.json.return_value = {
            "idToken": "test_id_token",
            "email": "test@example.com",
            "refreshToken": "test_refresh_token",
            "expiresIn": "3600",
            "localId": "user123",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        credentials = firebase_email_client.sign_in_with_email_password(
            "test@example.com", "password123"
        )

        assert credentials.id_token == "test_id_token"
        assert credentials.refresh_token == "test_refresh_token"
        assert credentials.user_email == "test@example.com"
        assert credentials.token_expiry > datetime.now(timezone.utc)
        
        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "signInWithPassword" in call_args[0][0]
        assert call_args[1]["json"]["email"] == "test@example.com"
        assert call_args[1]["json"]["password"] == "password123"

    @patch("src.cli.firebase_email_auth.requests.post")
    def test_sign_in_with_invalid_credentials(self, mock_post, firebase_email_client):
        """Test sign in with invalid credentials."""
        # Mock error response
        mock_response = Mock()
        mock_response.json.return_value = {
            "error": {"message": "INVALID_PASSWORD"}
        }
        mock_response.raise_for_status.side_effect = requests.HTTPError(response=mock_response)
        mock_post.return_value = mock_response

        with pytest.raises(DiscoveryCLIError, match="Incorrect password"):
            firebase_email_client.sign_in_with_email_password(
                "test@example.com", "wrong_password"
            )

    @patch("src.cli.firebase_email_auth.requests.post")
    def test_sign_in_with_nonexistent_email(self, mock_post, firebase_email_client):
        """Test sign in with non-existent email."""
        # Mock error response
        mock_response = Mock()
        mock_response.json.return_value = {
            "error": {"message": "EMAIL_NOT_FOUND"}
        }
        mock_response.raise_for_status.side_effect = requests.HTTPError(response=mock_response)
        mock_post.return_value = mock_response

        with pytest.raises(DiscoveryCLIError, match="No account found with this email"):
            firebase_email_client.sign_in_with_email_password(
                "nonexistent@example.com", "password123"
            )

    @patch("src.cli.firebase_email_auth.requests.post")
    def test_sign_up_with_email_password_success(self, mock_post, firebase_email_client):
        """Test successful account creation."""
        # Mock the sign-up response
        mock_response = Mock()
        mock_response.json.return_value = {
            "idToken": "new_id_token",
            "email": "newuser@example.com",
            "refreshToken": "new_refresh_token",
            "expiresIn": "3600",
            "localId": "newuser123",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        credentials = firebase_email_client.sign_up_with_email_password(
            "newuser@example.com", "securepassword"
        )

        assert credentials.id_token == "new_id_token"
        assert credentials.refresh_token == "new_refresh_token"
        assert credentials.user_email == "newuser@example.com"
        assert credentials.token_expiry > datetime.now(timezone.utc)
        
        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "signUp" in call_args[0][0]
        assert call_args[1]["json"]["email"] == "newuser@example.com"
        assert call_args[1]["json"]["password"] == "securepassword"

    @patch("src.cli.firebase_email_auth.requests.post")
    def test_sign_up_with_existing_email(self, mock_post, firebase_email_client):
        """Test sign up with already registered email."""
        # Mock error response
        mock_response = Mock()
        mock_response.json.return_value = {
            "error": {"message": "EMAIL_EXISTS"}
        }
        mock_response.raise_for_status.side_effect = requests.HTTPError(response=mock_response)
        mock_post.return_value = mock_response

        with pytest.raises(DiscoveryCLIError, match="account with this email already exists"):
            firebase_email_client.sign_up_with_email_password(
                "existing@example.com", "password123"
            )

    @patch("src.cli.firebase_email_auth.requests.post")
    def test_sign_up_with_weak_password(self, mock_post, firebase_email_client):
        """Test sign up with weak password."""
        # Mock error response
        mock_response = Mock()
        mock_response.json.return_value = {
            "error": {"message": "WEAK_PASSWORD"}
        }
        mock_response.raise_for_status.side_effect = requests.HTTPError(response=mock_response)
        mock_post.return_value = mock_response

        with pytest.raises(DiscoveryCLIError, match="Password is too weak"):
            firebase_email_client.sign_up_with_email_password(
                "user@example.com", "123"
            )

    @patch("src.cli.firebase_email_auth.requests.post")
    def test_refresh_id_token_success(self, mock_post, firebase_email_client):
        """Test successful token refresh."""
        # Mock the refresh response
        mock_response = Mock()
        mock_response.json.return_value = {
            "id_token": "refreshed_id_token",
            "refresh_token": "new_refresh_token",
            "expires_in": "3600",
            "user_id": "user123",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        credentials = firebase_email_client.refresh_id_token("old_refresh_token")

        assert credentials.id_token == "refreshed_id_token"
        assert credentials.refresh_token == "new_refresh_token"
        assert credentials.token_expiry > datetime.now(timezone.utc)
        
        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "securetoken.googleapis.com" in call_args[0][0]
        assert call_args[1]["json"]["refresh_token"] == "old_refresh_token"

    @patch("src.cli.firebase_email_auth.requests.post")
    def test_refresh_id_token_failure(self, mock_post, firebase_email_client):
        """Test token refresh failure."""
        # Mock error response
        mock_response = Mock()
        mock_response.json.return_value = {
            "error": {"message": "TOKEN_EXPIRED"}
        }
        mock_response.raise_for_status.side_effect = requests.HTTPError(response=mock_response)
        mock_post.return_value = mock_response

        with pytest.raises(DiscoveryCLIError, match="Token refresh failed"):
            firebase_email_client.refresh_id_token("expired_token")

    @patch("src.cli.firebase_email_auth.requests.post")
    def test_reset_password_success(self, mock_post, firebase_email_client):
        """Test successful password reset."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"email": "user@example.com"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Should not raise
        firebase_email_client.reset_password("user@example.com")
        
        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "sendOobCode" in call_args[0][0]
        assert call_args[1]["json"]["email"] == "user@example.com"
        assert call_args[1]["json"]["requestType"] == "PASSWORD_RESET"

    @patch("src.cli.firebase_email_auth.requests.post")
    def test_reset_password_failure(self, mock_post, firebase_email_client):
        """Test password reset failure."""
        # Mock error response
        mock_response = Mock()
        mock_response.json.return_value = {
            "error": {"message": "EMAIL_NOT_FOUND"}
        }
        mock_response.raise_for_status.side_effect = requests.HTTPError(response=mock_response)
        mock_post.return_value = mock_response

        with pytest.raises(DiscoveryCLIError, match="No account found"):
            firebase_email_client.reset_password("nonexistent@example.com")

    @patch("src.cli.firebase_email_auth.requests.post")
    def test_network_error_handling(self, mock_post, firebase_email_client):
        """Test network error handling."""
        mock_post.side_effect = requests.ConnectionError("Network error")

        with pytest.raises(DiscoveryCLIError, match="Network error during sign in"):
            firebase_email_client.sign_in_with_email_password(
                "user@example.com", "password"
            )

    def test_error_message_extraction(self, firebase_email_client):
        """Test friendly error message extraction."""
        # Create mock HTTP error
        mock_response = Mock()
        mock_response.json.return_value = {
            "error": {"message": "TOO_MANY_ATTEMPTS_TRY_LATER"}
        }
        
        exc = requests.HTTPError(response=mock_response)
        message = firebase_email_client._extract_error_message(exc)
        
        assert "Too many failed attempts" in message
