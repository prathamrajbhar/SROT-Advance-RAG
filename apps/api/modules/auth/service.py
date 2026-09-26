import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import get_settings
from core.security import (
    create_access_token,
    get_password_hash,
    hash_token,
    verify_password,
)
from models.auth import RefreshToken, User
from modules.auth.schemas import UserLoginRequest, UserRegisterRequest

settings = get_settings()


async def register_user(
    db: AsyncSession, request: UserRegisterRequest
) -> Tuple[User, str, str]:
    stmt = select(User).where(User.email == request.email.lower())
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    user = User(
        email=request.email.lower(),
        password_hash=get_password_hash(request.password),
        full_name=request.full_name,
    )
    db.add(user)
    await db.flush()

    access_token, refresh_raw = await _create_token_pair(db, user.id)
    await db.commit()
    await db.refresh(user)
    return user, access_token, refresh_raw


async def login_user(
    db: AsyncSession, request: UserLoginRequest
) -> Tuple[User, str, str]:
    stmt = select(User).where(User.email == request.email.lower())
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token, refresh_raw = await _create_token_pair(db, user.id)
    await db.commit()
    return user, access_token, refresh_raw


async def refresh_tokens(
    db: AsyncSession, refresh_raw: str
) -> Tuple[User, str, str]:
    token_h = hash_token(refresh_raw)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_h)
    token_record = (await db.execute(stmt)).scalar_one_or_none()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    now = datetime.now(timezone.utc)
    if token_record.revoked_at is not None:
        # Reuse attack detected: revoke entire token family
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == token_record.family_id)
            .values(revoked_at=now)
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token reuse detected. All sessions revoked.",
        )

    if token_record.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Revoke current token
    token_record.revoked_at = now

    user_stmt = select(User).where(User.id == token_record.user_id)
    user = (await db.execute(user_stmt)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    access_token, new_refresh_raw = await _create_token_pair(
        db, user.id, family_id=token_record.family_id
    )
    await db.commit()
    return user, access_token, new_refresh_raw


async def logout_user(db: AsyncSession, refresh_raw: Optional[str]) -> None:
    if not refresh_raw:
        return
    token_h = hash_token(refresh_raw)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_h)
    token_record = (await db.execute(stmt)).scalar_one_or_none()
    if token_record:
        now = datetime.now(timezone.utc)
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == token_record.family_id)
            .values(revoked_at=now)
        )
        await db.commit()


async def _create_token_pair(
    db: AsyncSession, user_id: uuid.UUID, family_id: Optional[uuid.UUID] = None
) -> Tuple[str, str]:
    fam_id = family_id or uuid.uuid4()
    refresh_raw = uuid.uuid4().hex + uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    token_record = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(refresh_raw),
        family_id=fam_id,
        expires_at=expires_at,
    )
    db.add(token_record)

    access_token = create_access_token(
        subject=str(user_id),
        extra_claims={"family_id": str(fam_id)},
    )
    return access_token, refresh_raw
