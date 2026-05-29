import logging

from redis import Redis
from rq import Queue

from app.core.config import settings

logger = logging.getLogger(__name__)

redis_conn = None
high_queue = None
default_queue = None
low_queue = None


def init_queues():
    global redis_conn, high_queue, default_queue, low_queue
    try:
        redis_conn = Redis.from_url(settings.redis_url)
        redis_conn.ping()
        high_queue = Queue("high", connection=redis_conn)
        default_queue = Queue("default", connection=redis_conn)
        low_queue = Queue("low", connection=redis_conn)
        logger.info("RQ queues initialized")
    except Exception as e:
        logger.warning(f"Redis not available, RQ queues disabled: {e}")


init_queues()
