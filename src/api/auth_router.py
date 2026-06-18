"""FastAPI router for authentication: register, token (login), refresh, logout, me."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..core.services.auth_service import AuthService
from ..core.commands.auth_commands import (
    RegisterUserCommand,
    LoginCommand,
    RefreshCommand,
    LogoutCommand,
    ChangePasswordCommand,
)
from .auth.config import get_auth_settings
from .auth.jwt_auth import get_current_user_email
from .dependencies.auth import get_auth_service
from .dtos import (
    RegisterRequest,
    UserResponse,
    TokenResponse,
    RefreshRequest,
    LogoutRequest,
    ChangePasswordRequest,
    ValidationErrorDetail,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _validation_error(result) -> HTTPException:
    """Map a failed Result to a 400 with the standard validation-error shape."""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": result.error,
            "validation_errors": [
                ValidationErrorDetail(field=e.field, message=e.message, code=e.code).model_dump()
                for e in result.validation_errors
            ],
        },
    )


def _to_user_response(user) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        roles=user.roles,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def _to_token_response(tokens) -> TokenResponse:
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Register a new user. Disabled when ALLOW_REGISTRATION is false."""
    if not get_auth_settings().allow_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-registration is disabled",
        )

    result = service.register(RegisterUserCommand(
        email=request.email,
        password=request.password,
        display_name=request.display_name,
    ))

    if result.is_failure:
        if result.validation_errors:
            raise _validation_error(result)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": result.error})

    return _to_user_response(result.value)


@router.post("/token", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
):
    """OAuth2 password-grant token endpoint. `username` is the user's email."""
    result = service.authenticate(LoginCommand(
        email=form_data.username,
        password=form_data.password,
    ))

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.error,
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _to_token_response(result.value)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Exchange a refresh token for a new token pair (rotates the refresh token)."""
    result = service.refresh(RefreshCommand(refresh_token=request.refresh_token))

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.error,
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _to_token_response(result.value)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: LogoutRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Revoke a refresh token (idempotent)."""
    result = service.logout(LogoutCommand(refresh_token=request.refresh_token))
    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": result.error},
        )
    return None


@router.get("/me", response_model=UserResponse)
def me(
    current_user_email: str = Depends(get_current_user_email),
    service: AuthService = Depends(get_auth_service),
):
    """Return the currently authenticated user."""
    result = service.get_user_by_email(current_user_email)
    if result.is_failure or result.value is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _to_user_response(result.value)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    request: ChangePasswordRequest,
    current_user_email: str = Depends(get_current_user_email),
    service: AuthService = Depends(get_auth_service),
):
    """Change the authenticated user's password; revokes all refresh tokens."""
    result = service.change_password(ChangePasswordCommand(
        email=current_user_email,
        old_password=request.old_password,
        new_password=request.new_password,
    ))

    if result.is_failure:
        if result.validation_errors:
            raise _validation_error(result)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=result.error)

    return None
