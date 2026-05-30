import hashlib
import hmac

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.core.security import decode_token, hash_password
from app.models.badge import UserBadge
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import SocialLinkOut, UserBadgeBrief, UserOut
from app.services import auth_service
from app.services.auth_service import _generate_referral_code
from app.services.notification_service import create_notification
from app.services.user_service import get_user_by_id


class TelegramAuthRequest(BaseModel):
    id: int
    first_name: str
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str

class SetPinRequest(BaseModel):
    pin: str

class CheckPinRequest(BaseModel):
    email: str

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_to_out(user):
    try:
        sl = getattr(user, 'social_links', [])
        if sl is None:
            sl = []
    except Exception:
        sl = []
    try:
        ub_list = getattr(user, 'badges', None) or []
    except Exception:
        ub_list = []
    badges_out = []
    active_badge = None
    for ub in ub_list:
        if ub.badge:
            brief = UserBadgeBrief(id=ub.badge.id, name=ub.badge.name, icon_svg=ub.badge.icon_svg, description=ub.badge.description, avatar_ring_gradient=ub.badge.avatar_ring_gradient, avatar_ring_effect=ub.badge.avatar_ring_effect, is_active=ub.is_active)
            badges_out.append(brief)
            if ub.is_active:
                active_badge = brief
    return UserOut(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        username=user.username,
        bio=user.bio,
        avatar_url=user.avatar_url,
        is_public=user.is_public,
        is_email_confirmed=user.is_email_confirmed,
        created_at=user.created_at,
        social_links=[SocialLinkOut(platform=l.platform, url=l.url) for l in sl],
        settings=user.settings or {},
        is_admin=user.is_admin,
        referral_code=user.referral_code or "",
        referrals_count=user.referrals_count or 0,
        storage_limit=user.storage_limit,
        storage_used=user.storage_used,
        badges=badges_out,
        active_badge=active_badge,
    )


async def _sync_admin_flag(session: AsyncSession, user: User):
    admin_emails = [e.strip().lower() for e in settings.admin_emails.split(",") if e.strip()]
    should_be_admin = user.email.lower() in admin_emails
    if user.is_admin != should_be_admin:
        user.is_admin = should_be_admin
        await session.flush()


def _token_response(user: User, access: str, refresh: str) -> TokenResponse:
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=_user_to_out(user),
        has_pin=user.pin_hash is not None,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, session: AsyncSession = Depends(get_session)):
    try:
        user = await auth_service.register_user(session, body.email, body.password, body.nickname, body.username, body.referral_code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    await _sync_admin_flag(session, user)
    if not user.pin_hash:
        await create_notification(
            session, user.id, "setup_pin",
            "Настоятельно рекомендуем установить PIN-код в настройках аккаунта. "
            "Он потребуется для восстановления пароля."
        )
    access, refresh = auth_service.generate_tokens(user.id)
    await auth_service.store_refresh_token(session, user.id, refresh)
    await session.commit()
    return _token_response(user, access, refresh)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session)):
    try:
        user = await auth_service.authenticate_user(session, body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    await _sync_admin_flag(session, user)
    if not user.pin_hash:
        await create_notification(
            session, user.id, "setup_pin",
            "Настоятельно рекомендуем установить PIN-код в настройках аккаунта. "
            "Он потребуется для восстановления пароля."
        )
    access, refresh = auth_service.generate_tokens(user.id)
    await auth_service.store_refresh_token(session, user.id, refresh)
    await session.commit()
    return _token_response(user, access, refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, session: AsyncSession = Depends(get_session)):
    try:
        access, new_refresh = await auth_service.rotate_refresh_token(session, body.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    user_id = decode_token(access).get("sub", "")
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return _token_response(user, access, new_refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, session: AsyncSession = Depends(get_session)):
    await auth_service.revoke_refresh_token(session, body.refresh_token)


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)):
    return {"message": "Используйте /reset-password для смены пароля"}


class ResetPasswordDirectRequest(BaseModel):
    login: str
    new_password: str
    pin: str | None = None


@router.post("/reset-password")
async def reset_password(body: ResetPasswordDirectRequest, session: AsyncSession = Depends(get_session)):
    success = await auth_service.reset_password_direct(session, body.login, body.new_password, body.pin)
    await session.commit()
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь не найден, неверный PIN-код, либо PIN не установлен")
    return {"message": "Пароль изменён"}


@router.post("/check-pin")
async def check_pin(body: CheckPinRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    return {"has_pin": user is not None and user.pin_hash is not None}


def _get_current_user_or_none(session: AsyncSession, token: str | None) -> User | None:
    if not token:
        return None
    try:
        payload = decode_token(token)
        user_id = payload.get("sub", "")
        if not user_id:
            return None
        result = session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    except Exception:
        return None


@router.put("/pin")
async def set_pin(
    body: SetPinRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if len(body.pin) < 4 or len(body.pin) > 6 or not body.pin.isdigit():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PIN должен быть 4-6 цифр")
    current_user.pin_hash = hash_password(body.pin)
    await session.commit()
    return {"ok": True}


@router.get("/telegram-config")
async def telegram_config():
    bot_token = settings.telegram_bot_token
    bot_id = bot_token.split(":")[0] if bot_token and ":" in bot_token else None
    return {
        "bot_username": settings.telegram_bot_username or None,
        "bot_id": bot_id,
    }


def _verify_telegram_hash(data: dict, bot_token: str) -> bool:
    check_hash = data.pop("hash", "")
    items = sorted(data.items())
    check_string = "\n".join(f"{k}={v}" for k, v in items)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    computed = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    return computed == check_hash


@router.post("/telegram", response_model=TokenResponse)
async def telegram_auth(body: TelegramAuthRequest, session: AsyncSession = Depends(get_session)):
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram auth not configured")

    data = body.model_dump()
    if not _verify_telegram_hash(dict(data), settings.telegram_bot_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram hash")

    telegram_id = str(body.id)

    result = await session.execute(
        select(User).options(selectinload(User.social_links)).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        nickname = body.first_name
        username = body.username or f"tg_{body.id}"
        base_username = username
        suffix = 1
        while True:
            exists = await session.execute(select(User).where(User.username == username))
            if not exists.scalar_one_or_none():
                break
            username = f"{base_username}_{suffix}"
            suffix += 1

        # Generate unique referral code
        while True:
            code = _generate_referral_code()
            exists = await session.execute(select(User).where(User.referral_code == code))
            if not exists.scalar_one_or_none():
                break

        user = User(
            email=f"tg_{telegram_id}@placeholder.local",
            password_hash="",
            nickname=nickname,
            username=username,
            telegram_id=telegram_id,
            telegram_username=body.username,
            avatar_url=body.photo_url,
            is_email_confirmed=True,
            referral_code=code,
        )
        session.add(user)
        await session.flush()

    access, refresh = auth_service.generate_tokens(user.id)
    await auth_service.store_refresh_token(session, user.id, refresh)
    await session.commit()
    return _token_response(user, access, refresh)
