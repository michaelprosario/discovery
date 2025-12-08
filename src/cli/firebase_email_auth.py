"""Firebase email/password authentication (no OAuth required)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import requests
from pydantic import BaseModel

from .config_store import FirebaseCredentials
from .exceptions import DiscoveryCLIError
from .output import console


class FirebaseAuthResponse(BaseModel):
    """Response from Firebase authentication."""

    idToken: str
    email: str
    refreshToken: str
    expiresIn: str
    localId: str
    registered: Optional[bool] = None


class FirebaseEmailAuthClient:
    """Firebase authentication using email/password (no OAuth required)."""

    def __init__(self, api_key: str):
        """
        Initialize Firebase email auth client.

        Args:
            api_key: Firebase Web API key
        """
        self.api_key = api_key
        self.base_url = "https://identitytoolkit.googleapis.com/v1/accounts"

    def sign_in_with_email_password(
        self, email: str, password: str
    ) -> FirebaseCredentials:
        """
        Sign in with email and password.

        Args:
            email: User email address
            password: User password

        Returns:
            FirebaseCredentials with ID token and refresh token
        """
        url = f"{self.base_url}:signInWithPassword?key={self.api_key}"

        try:
            response = requests.post(
                url,
                json={
                    "email": email,
                    "password": password,
                    "returnSecureToken": True,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = FirebaseAuthResponse(**response.json())

            # Calculate expiry
            expires_in_seconds = int(data.expiresIn)
            expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)

            return FirebaseCredentials(
                id_token=data.idToken,
                refresh_token=data.refreshToken,
                token_expiry=expiry,
                user_email=data.email,
            )

        except requests.HTTPError as exc:
            error_msg = self._extract_error_message(exc)
            raise DiscoveryCLIError(f"Sign in failed: {error_msg}") from exc
        except requests.RequestException as exc:
            raise DiscoveryCLIError(f"Network error during sign in: {exc}") from exc

    def sign_up_with_email_password(
        self, email: str, password: str
    ) -> FirebaseCredentials:
        """
        Create new account with email and password.

        Args:
            email: Email address for new account
            password: Password for new account

        Returns:
            FirebaseCredentials with ID token and refresh token
        """
        url = f"{self.base_url}:signUp?key={self.api_key}"

        try:
            response = requests.post(
                url,
                json={
                    "email": email,
                    "password": password,
                    "returnSecureToken": True,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = FirebaseAuthResponse(**response.json())

            # Calculate expiry
            expires_in_seconds = int(data.expiresIn)
            expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)

            return FirebaseCredentials(
                id_token=data.idToken,
                refresh_token=data.refreshToken,
                token_expiry=expiry,
                user_email=data.email,
            )

        except requests.HTTPError as exc:
            error_msg = self._extract_error_message(exc)
            raise DiscoveryCLIError(f"Sign up failed: {error_msg}") from exc
        except requests.RequestException as exc:
            raise DiscoveryCLIError(f"Network error during sign up: {exc}") from exc

    def refresh_id_token(self, refresh_token: str) -> FirebaseCredentials:
        """
        Refresh the ID token using refresh token.

        Args:
            refresh_token: Refresh token from previous authentication

        Returns:
            FirebaseCredentials with new ID token
        """
        url = f"https://securetoken.googleapis.com/v1/token?key={self.api_key}"

        try:
            response = requests.post(
                url,
                json={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            # Calculate expiry
            expires_in_seconds = int(data.get("expires_in", 3600))
            expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)

            return FirebaseCredentials(
                id_token=data["id_token"],
                refresh_token=data["refresh_token"],
                token_expiry=expiry,
                user_email="",  # Not returned in refresh response
            )

        except requests.HTTPError as exc:
            error_msg = self._extract_error_message(exc)
            raise DiscoveryCLIError(f"Token refresh failed: {error_msg}") from exc
        except requests.RequestException as exc:
            raise DiscoveryCLIError(f"Network error during token refresh: {exc}") from exc

    def reset_password(self, email: str) -> None:
        """
        Send password reset email.

        Args:
            email: Email address to send reset link to
        """
        url = f"{self.base_url}:sendOobCode?key={self.api_key}"

        try:
            response = requests.post(
                url,
                json={
                    "requestType": "PASSWORD_RESET",
                    "email": email,
                },
                timeout=10,
            )
            response.raise_for_status()

        except requests.HTTPError as exc:
            error_msg = self._extract_error_message(exc)
            raise DiscoveryCLIError(f"Password reset failed: {error_msg}") from exc
        except requests.RequestException as exc:
            raise DiscoveryCLIError(
                f"Network error during password reset: {exc}"
            ) from exc

    def _extract_error_message(self, exc: requests.HTTPError) -> str:
        """Extract user-friendly error message from Firebase error response."""
        try:
            error_data = exc.response.json()
            if "error" in error_data:
                error_info = error_data["error"]
                if isinstance(error_info, dict):
                    message = error_info.get("message", str(exc))
                    # Make Firebase error messages more user-friendly
                    friendly_messages = {
                        "EMAIL_NOT_FOUND": "No account found with this email address",
                        "INVALID_PASSWORD": "Incorrect password",
                        "USER_DISABLED": "This account has been disabled",
                        "EMAIL_EXISTS": "An account with this email already exists",
                        "WEAK_PASSWORD": "Password is too weak (minimum 6 characters)",
                        "INVALID_EMAIL": "Invalid email address",
                        "TOO_MANY_ATTEMPTS_TRY_LATER": "Too many failed attempts. Please try again later",
                    }
                    return friendly_messages.get(message, message)
                return str(error_info)
            return str(exc)
        except (ValueError, KeyError):
            return str(exc)


__all__ = ["FirebaseEmailAuthClient", "FirebaseAuthResponse"]
