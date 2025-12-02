"""Firebase authentication module for Discovery API."""
from .firebase_auth import (
    get_current_user_email,
    get_optional_user_email,
    initialize_firebase
)
from .authorization import (
    require_resource_owner,
    require_resource_owner_or_fail
)

__all__ = [
    "get_current_user_email",
    "get_optional_user_email",
    "initialize_firebase",
    "require_resource_owner",
    "require_resource_owner_or_fail"
]
