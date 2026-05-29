from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import Follow, SocialLink, User


async def get_user_by_id(session: AsyncSession, user_id: str) -> User | None:
    result = await session.execute(
        select(User).options(selectinload(User.social_links)).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def update_user(session: AsyncSession, user_id: str, data: dict) -> User | None:
    user = await get_user_by_id(session, user_id)
    if not user:
        return None
    for key, value in data.items():
        if value is not None and hasattr(user, key):
            setattr(user, key, value)
    return user


async def update_social_links(session: AsyncSession, user_id: str, links: list[dict]) -> list[SocialLink]:
    result = await session.execute(select(SocialLink).where(SocialLink.user_id == user_id))
    existing = result.scalars().all()
    for link in existing:
        await session.delete(link)
    new_links = [SocialLink(user_id=user_id, platform=l["platform"], url=l["url"]) for l in links]
    for nl in new_links:
        session.add(nl)
    await session.flush()
    for nl in new_links:
        await session.refresh(nl)
    return new_links


async def follow_user(session: AsyncSession, follower_id: str, following_id: str) -> Follow | None:
    if follower_id == following_id:
        return None
    result = await session.execute(
        select(Follow).where(
            Follow.follower_id == follower_id,
            Follow.following_id == following_id,
        )
    )
    if result.scalar_one_or_none():
        return None
    follow = Follow(follower_id=follower_id, following_id=following_id)
    session.add(follow)
    await session.flush()
    await session.refresh(follow)
    return follow


async def unfollow_user(session: AsyncSession, follower_id: str, following_id: str) -> bool:
    result = await session.execute(
        select(Follow).where(
            Follow.follower_id == follower_id,
            Follow.following_id == following_id,
        )
    )
    follow = result.scalar_one_or_none()
    if not follow:
        return False
    await session.delete(follow)
    return True


async def get_followers(session: AsyncSession, user_id: str) -> list[User]:
    result = await session.execute(
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.following_id == user_id)
        .order_by(Follow.created_at.desc())
    )
    return list(result.scalars().all())


async def get_following(session: AsyncSession, user_id: str) -> list[User]:
    result = await session.execute(
        select(User)
        .join(Follow, Follow.following_id == User.id)
        .where(Follow.follower_id == user_id)
        .order_by(Follow.created_at.desc())
    )
    return list(result.scalars().all())


async def get_follower_count(session: AsyncSession, user_id: str) -> int:
    result = await session.execute(
        select(Follow).where(Follow.following_id == user_id)
    )
    return len(result.scalars().all())


async def get_following_count(session: AsyncSession, user_id: str) -> int:
    result = await session.execute(
        select(Follow).where(Follow.follower_id == user_id)
    )
    return len(result.scalars().all())


async def is_following(session: AsyncSession, follower_id: str, following_id: str) -> bool:
    result = await session.execute(
        select(Follow).where(
            Follow.follower_id == follower_id,
            Follow.following_id == following_id,
        )
    )
    return result.scalar_one_or_none() is not None
