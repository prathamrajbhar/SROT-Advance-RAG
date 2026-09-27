from typing import Optional
from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import get_settings
from core.database import get_db
from models.auth import User
from modules.auth.deps import get_current_user
from modules.auth.schemas import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from modules.auth.service import (
    login_user,
    logout_user,
    refresh_tokens,
    register_user,
)

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Auth"])

REFRESH_COOKIE_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
IS_PRODUCTION = settings.ENVIRONMENT.lower() == "production"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=IS_PRODUCTION,
        path="/",
        max_age=REFRESH_COOKIE_MAX_AGE,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user, access_token, refresh_raw = await register_user(db, request)
    _set_refresh_cookie(response, refresh_raw)
    return TokenResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user, access_token, refresh_raw = await login_user(db, request)
    _set_refresh_cookie(response, refresh_raw)
    return TokenResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user, access_token, new_refresh_raw = await refresh_tokens(db, refresh_token or "")
    _set_refresh_cookie(response, new_refresh_raw)
    return TokenResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> None:
    await logout_user(db, refresh_token)
    response.delete_cookie(key="refresh_token", path="/")


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)

