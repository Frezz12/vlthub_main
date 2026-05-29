import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.auth import EmailConfirmation, RefreshToken
from app.models.user import User


async def register_user(session: AsyncSession, email: str, password: str, nickname: str, username: str) -> User:
    existing = await session.execute(select(User).where((User.email == email) | (User.username == username)))
    if existing.first():
        raise ValueError("Email or username already taken")
    user = User(email=email, password_hash=hash_password(password), nickname=nickname, username=username)
    session.add(user)
    await session.flush()
    await session.refresh(user, ["social_links"])
    return user


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User:
    result = await session.execute(
        select(User).options(selectinload(User.social_links)).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")
    return user


def generate_tokens(user_id: str) -> tuple[str, str]:
    access = create_access_token(user_id)
    refresh = create_refresh_token(user_id)
    return access, refresh


async def store_refresh_token(session: AsyncSession, user_id: str, token: str) -> None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    rt = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires)
    session.add(rt)


async def rotate_refresh_token(session: AsyncSession, old_token: str) -> tuple[str, str]:
    token_hash = hashlib.sha256(old_token.encode()).hexdigest()
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash, RefreshToken.expires_at > datetime.now(timezone.utc))
    )
    rt = result.scalar_one_or_none()
    if not rt:
        raise ValueError("Invalid or expired refresh token")
    await session.delete(rt)
    user_id = rt.user_id
    access, new_refresh = generate_tokens(user_id)
    await store_refresh_token(session, user_id, new_refresh)
    return access, new_refresh


async def revoke_refresh_token(session: AsyncSession, token: str) -> None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    result = await session.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    rt = result.scalar_one_or_none()
    if rt:
        await session.delete(rt)


async def reset_password_direct(session: AsyncSession, login: str, new_password: str, pin: str | None = None) -> bool:
    result = await session.execute(
        select(User).where(User.email == login)
    )
    user = result.scalar_one_or_none()
    if not user:
        return False
    if not user.pin_hash:
        return False
    if not pin or not verify_password(pin, user.pin_hash):
        return False
    user.password_hash = hash_password(new_password)
    return True
