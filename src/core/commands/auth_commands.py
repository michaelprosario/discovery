"""Command objects for authentication operations following CQRS pattern."""
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class RegisterUserCommand:
    """Command to register a new user."""

    email: str
    password: str
    display_name: Optional[str] = None
    roles: Optional[List[str]] = None


@dataclass
class LoginCommand:
    """Command to authenticate a user with email + password (OAuth2 password grant)."""

    email: str
    password: str


@dataclass
class RefreshCommand:
    """Command to exchange a refresh token for a new token pair."""

    refresh_token: str


@dataclass
class LogoutCommand:
    """Command to revoke a refresh token."""

    refresh_token: str


@dataclass
class ChangePasswordCommand:
    """Command to change the password of an authenticated user."""

    email: str
    old_password: str
    new_password: str
