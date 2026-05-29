import logging

from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_pool = None
_redis_client = None


def get_pool():
    global _pool
    if _pool is None:
        try:
            _pool = ConnectionPool.from_url(settings.redis_url)
        except Exception as e:
            logger.warning(f"Redis pool init failed: {e}")
            _pool = None
    return _pool


def get_redis_client():
    global _redis_client
    if _redis_client is None:
        pool = get_pool()
        if pool:
            _redis_client = Redis.from_pool(pool)
    return _redis_client


async def get_redis() -> Redis | None:
    return get_redis_client()
