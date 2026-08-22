from collections.abc import Generator

from redis import Redis

from .config import get_settings


def get_redis() -> Generator[Redis, None, None]:
    client = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        yield client
    finally:
        client.close()
