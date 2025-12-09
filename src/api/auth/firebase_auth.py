"""Firebase authentication dependencies for FastAPI."""
import json
import os
from functools import lru_cache
from typing import Optional

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

# System user email for API key authentication
SYSTEM_USER_EMAIL = "api_key_user@system"

# Firebase admin is imported lazily to allow the app to start without Firebase configured
_firebase_initialized = False


@lru_cache()
def initialize_firebase() -> bool:
    """
    Initialize Firebase Admin SDK.
    
    Uses environment variables for configuration:
    - FIREBASE_CREDENTIALS_PATH: Path to service account JSON file
    - FIREBASE_SERVICE_ACCOUNT_JSON: Direct JSON content (alternative)
    
    Returns:
        bool: True if Firebase was initialized, False if not configured
    """
    global _firebase_initialized
    
    if _firebase_initialized:
        return True
    
    try:
        import firebase_admin
        from firebase_admin import credentials
        
        if firebase_admin._apps:
            _firebase_initialized = True
            return True
        
        credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
        service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
        
        if credentials_path and os.path.exists(credentials_path):
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            return True
        elif service_account_json:
            cred = credentials.Certificate(json.loads(service_account_json))
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            return True
        else:
            # Firebase not configured - this is okay for development
            return False
            
    except ImportError:
        # firebase-admin not installed
        return False
    except Exception:
        # Other initialization errors
        return False


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
    if not initialize_firebase():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not configured",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        from firebase_admin import auth
        
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
        
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        error_type = type(e).__name__
        if "InvalidIdToken" in error_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif "ExpiredIdToken" in error_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif "RevokedIdToken" in error_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
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
    """
    if not credentials:
        return None
    
    if not initialize_firebase():
        return None
    
    try:
        from firebase_admin import auth
        
        decoded_token = auth.verify_id_token(credentials.credentials)
        return decoded_token.get('email')
    except Exception:
        return None


async def get_current_user_email_with_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    x_api_key: Optional[str] = Header(None)
) -> str:
    """
    Dual authentication: Firebase ID token (primary) or static API key (fallback).
    
    Attempts Firebase authentication first. If no token or token is invalid,
    checks for X-API-Key header against STATIC_API_KEY environment variable.
    
    Args:
        credentials: HTTP Bearer token from request header (optional)
        x_api_key: API key from X-API-Key header (optional)
        
    Returns:
        str: User's email from Firebase token, or system user email for API key
        
    Raises:
        HTTPException: If both authentication methods fail
    """
    # Try Firebase authentication first
    if credentials:
        if initialize_firebase():
            try:
                from firebase_admin import auth
                
                decoded_token = auth.verify_id_token(credentials.credentials)
                email = decoded_token.get('email')
                
                if email:
                    return email
            except Exception:
                # Firebase auth failed, will try API key next
                pass
    
    # Try API key authentication as fallback
    static_api_key = os.getenv('STATIC_API_KEY')
    
    if static_api_key and x_api_key and x_api_key == static_api_key:
        return SYSTEM_USER_EMAIL
    
    # Both authentication methods failed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide either a valid Firebase ID token or X-API-Key header.",
        headers={"WWW-Authenticate": "Bearer"},
    )

