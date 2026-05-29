from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.core.security import decode_token
from app.models.badge import UserBadge
from app.models.user import SocialLink, User

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    session: AsyncSession = Depends(get_session),
    token_data: str | None = Depends(security_scheme),
) -> User:
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return await _resolve_user(session, token_data.credentials)


async def get_optional_user(
    session: AsyncSession = Depends(get_session),
    token_data: str | None = Depends(security_scheme),
) -> User | None:
    if not token_data:
        return None
    return await _resolve_user(session, token_data.credentials)


async def _resolve_user(session: AsyncSession, token: str) -> User:
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    result = await session.execute(
        select(User)
        .options(selectinload(User.social_links))
        .options(selectinload(User.badges).selectinload(UserBadge.badge))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
