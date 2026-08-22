import asyncio
from dataclasses import dataclass
from math import ceil
from typing import Protocol

from redis import Redis
from redis.exceptions import RedisError


class RateLimitBackendUnavailable(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int


class CredentialRateLimiter(Protocol):
    async def check(self, key: str, *, limit: int, window_seconds: int) -> RateLimitDecision: ...


class RedisFixedWindowRateLimiter:
    _SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('PEXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('PTTL', KEYS[1])
return {current, ttl}
"""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def check(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        return await asyncio.to_thread(
            self._check_sync,
            key,
            limit,
            window_seconds,
        )

    def _check_sync(self, key: str, limit: int, window_seconds: int) -> RateLimitDecision:
        try:
            raw = self._redis.eval(
                self._SCRIPT,
                1,
                key,
                window_seconds * 1_000,
            )
        except RedisError as exc:
            raise RateLimitBackendUnavailable() from exc

        if not isinstance(raw, list) or len(raw) != 2:
            raise RateLimitBackendUnavailable()

        count = int(raw[0])
        ttl_ms = max(int(raw[1]), 0)
        retry_after_seconds = max(1, ceil(ttl_ms / 1_000))
        return RateLimitDecision(
            allowed=count <= limit,
            retry_after_seconds=retry_after_seconds,
        )
