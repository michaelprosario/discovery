"""Firebase authentication dependencies for FastAPI."""
import json
import os
from functools import lru_cache
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


@lru_cache()
def initialize_firebase() -> None:
    """
    Initialize Firebase Admin SDK.

    Uses environment variables for configuration:
    - FIREBASE_CREDENTIALS_PATH: Path to service account JSON file
    - FIREBASE_SERVICE_ACCOUNT_JSON: Direct JSON content (alternative)

    Raises:
        RuntimeError: If Firebase credentials are not configured
    """
    import firebase_admin
    from firebase_admin import credentials

    if firebase_admin._apps:
        return  # Already initialized

    credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
    service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')

    if credentials_path and os.path.exists(credentials_path):
        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred)
    elif service_account_json:
        cred = credentials.Certificate(json.loads(service_account_json))
        firebase_admin.initialize_app(cred)
    else:
        raise RuntimeError(
            "Firebase credentials not configured. Set FIREBASE_CREDENTIALS_PATH "
            "or FIREBASE_SERVICE_ACCOUNT_JSON environment variable."
        )


async def get_current_user_email(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Verify Firebase ID token and extract user email.

    Args:
        credentials: HTTP Bearer token from request header

    Returns:
        str: User's email address from verified token

    Raises:
        HTTPException: If token is invalid or missing
    """
    from firebase_admin import auth

    initialize_firebase()

    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(credentials.credentials)

        # Extract email from token
        email = decoded_token.get('email')

        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not found in token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return email

    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user_email(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)
) -> Optional[str]:
    """
    Optional authentication - returns email if token present and valid, None otherwise.

    Useful for endpoints that work differently for authenticated vs anonymous users.

    Args:
        credentials: Optional HTTP Bearer token from request header

    Returns:
        Optional[str]: User's email address or None if not authenticated
    """
    if not credentials:
        return None

    try:
        return await get_current_user_email(credentials)
    except HTTPException:
        return None
