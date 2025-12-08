"""Firebase authentication client for CLI."""

from __future__ import annotations

import json
import os
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Optional
from urllib.parse import parse_qs, urlparse

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from .config_store import FirebaseCredentials
from .exceptions import DiscoveryCLIError
from .output import console

# Firebase scopes for authentication
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]

# Firebase REST API endpoints
FIREBASE_TOKEN_EXCHANGE_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp"
FIREBASE_TOKEN_REFRESH_URL = "https://securetoken.googleapis.com/v1/token"


class FirebaseAuthClient:
    """Manages Firebase authentication for CLI."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize Firebase auth client.
        
        Args:
            api_key: Firebase Web API key (from Firebase project settings)
        """
        self.api_key = api_key or os.getenv("FIREBASE_WEB_API_KEY")
        if not self.api_key:
            raise DiscoveryCLIError(
                "Firebase Web API key not configured. Set FIREBASE_WEB_API_KEY environment variable "
                "or pass api_key parameter."
            )

    def login(self, use_device_flow: bool = False) -> FirebaseCredentials:
        """
        Initiate Google Sign-In and return Firebase credentials.
        
        Args:
            use_device_flow: Use device flow instead of local redirect (for headless environments)
            
        Returns:
            FirebaseCredentials with ID token, refresh token, and expiry
        """
        console.print("[bold blue]Starting Google Sign-In...[/bold blue]")
        
        # Get OAuth client configuration
        client_config = self._get_oauth_client_config()
        
        if use_device_flow:
            credentials = self._device_flow_login(client_config)
        else:
            credentials = self._local_redirect_flow_login(client_config)
        
        # Exchange Google OAuth token for Firebase ID token
        firebase_creds = self._exchange_for_firebase_token(credentials)
        
        console.print(f"[green]✓ Successfully authenticated as {firebase_creds.user_email}[/green]")
        return firebase_creds

    def refresh_token(self, credentials: FirebaseCredentials) -> FirebaseCredentials:
        """
        Refresh an expired Firebase ID token.
        
        Args:
            credentials: Current Firebase credentials with refresh token
            
        Returns:
            Updated FirebaseCredentials with new ID token
        """
        # Use the email auth client for refresh (same API)
        from .firebase_email_auth import FirebaseEmailAuthClient
        
        email_client = FirebaseEmailAuthClient(self.api_key)
        new_creds = email_client.refresh_id_token(credentials.refresh_token)
        
        # Preserve email from original credentials
        new_creds.user_email = credentials.user_email
        
        return new_creds

    def get_valid_token(self, credentials: FirebaseCredentials) -> str:
        """
        Get current token, refreshing if necessary.
        
        Args:
            credentials: Firebase credentials to check
            
        Returns:
            Valid ID token
        """
        # Check if token is expired or will expire in next 5 minutes
        now = datetime.now(timezone.utc)
        buffer = timedelta(minutes=5)
        
        if credentials.token_expiry <= now + buffer:
            console.print("[yellow]Refreshing expired token...[/yellow]")
            new_creds = self.refresh_token(credentials)
            return new_creds.id_token
        
        return credentials.id_token

    def _get_oauth_client_config(self) -> Dict:
        """
        Get OAuth client configuration for Google Sign-In.
        
        Returns:
            OAuth client configuration dictionary
        """
        # This should be configured via environment or stored securely
        # For now, we'll use environment variables
        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            raise DiscoveryCLIError(
                "Google OAuth credentials not configured. Set GOOGLE_OAUTH_CLIENT_ID "
                "and GOOGLE_OAUTH_CLIENT_SECRET environment variables."
            )
        
        return {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8080", "urn:ietf:wg:oauth:2.0:oob"],
            }
        }

    def _local_redirect_flow_login(self, client_config: Dict) -> Credentials:
        """
        Perform OAuth login using local redirect flow.
        
        Args:
            client_config: OAuth client configuration
            
        Returns:
            Google OAuth credentials
        """
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        
        # Use local server for OAuth callback
        # Note: In dev containers, disable state validation to prevent CSRF mismatches
        # caused by browser/container separation
        try:
            credentials = flow.run_local_server(
                port=8080,
                authorization_prompt_message="Opening browser for Google Sign-In...",
                success_message="Authentication successful! You can close this window.",
                open_browser=True,
            )
        except Exception as e:
            # If state mismatch occurs, suggest using device flow
            if "mismatching_state" in str(e).lower() or "state not equal" in str(e).lower():
                raise DiscoveryCLIError(
                    "OAuth state mismatch detected. This often happens in dev containers or "
                    "remote environments.\n\n"
                    "Please try using device flow instead:\n"
                    "  discovery auth login --device-flow\n\n"
                    f"Original error: {e}"
                ) from e
            raise
        
        return credentials

    def _device_flow_login(self, client_config: Dict) -> Credentials:
        """
        Perform OAuth login using device flow (for headless environments).
        
        Args:
            client_config: OAuth client configuration
            
        Returns:
            Google OAuth credentials
        """
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        
        # Use console-based device flow
        credentials = flow.run_console()
        
        return credentials

    def _exchange_for_firebase_token(self, google_credentials: Credentials) -> FirebaseCredentials:
        """
        Exchange Google OAuth credentials for Firebase ID token.
        
        Args:
            google_credentials: Google OAuth credentials
            
        Returns:
            FirebaseCredentials with Firebase ID token
        """
        # Get the ID token from Google credentials
        id_token = google_credentials.id_token
        
        if not id_token:
            raise DiscoveryCLIError("No ID token found in Google credentials")
        
        # Exchange Google ID token for Firebase custom token
        url = f"{FIREBASE_TOKEN_EXCHANGE_URL}?key={self.api_key}"
        
        payload = {
            "postBody": f"id_token={id_token}&providerId=google.com",
            "requestUri": "http://localhost",
            "returnIdpCredential": True,
            "returnSecureToken": True,
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract Firebase tokens
            firebase_id_token = data["idToken"]
            firebase_refresh_token = data["refreshToken"]
            expires_in = int(data.get("expiresIn", 3600))
            
            # Get user email from token
            user_email = data.get("email", google_credentials.token.get("email", "unknown"))
            
            # Calculate expiry
            expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            
            return FirebaseCredentials(
                id_token=firebase_id_token,
                refresh_token=firebase_refresh_token,
                token_expiry=expiry,
                user_email=user_email,
            )
        except requests.RequestException as exc:
            raise DiscoveryCLIError(f"Failed to exchange token for Firebase: {exc}") from exc


__all__ = ["FirebaseAuthClient", "FirebaseCredentials"]
