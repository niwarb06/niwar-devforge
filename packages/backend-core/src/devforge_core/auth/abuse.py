from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

from redis import Redis
from redis.exceptions import RedisError

_FIXED_WINDOW_SCRIPT = """
local current = redis.call("INCR", KEYS[1])
if current == 1 then
  redis.call("EXPIRE", KEYS[1], ARGV[1])
end
local ttl = redis.call("TTL", KEYS[1])
return {current, ttl}
"""


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int


class RateLimitBackendUnavailable(RuntimeError):
    """Raised when abuse protection cannot safely reach its backing store."""


class RateLimiter(Protocol):
    def check(
        self,
        scope: str,
        subject: str,
        *,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision: ...


class RedisFixedWindowRateLimiter:
    """Distributed fixed-window limiter with hashed subject identifiers."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    def check(
        self,
        scope: str,
        subject: str,
        *,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        if limit < 1:
            raise ValueError("rate_limit_must_be_positive")
        if window_seconds < 1:
            raise ValueError("rate_limit_window_must_be_positive")

        fingerprint = sha256(subject.strip().lower().encode("utf-8")).hexdigest()
        key = f"devforge:ratelimit:{scope}:{fingerprint}"

        try:
            raw_result: object = self._client.eval(
                _FIXED_WINDOW_SCRIPT,
                1,
                key,
                window_seconds,
            )
            if not isinstance(raw_result, (list, tuple)) or len(raw_result) != 2:
                raise TypeError("unexpected_rate_limit_result")

            current = _as_int(raw_result[0])
            ttl = _as_int(raw_result[1])
        except (RedisError, TypeError, ValueError) as exc:
            raise RateLimitBackendUnavailable("rate_limit_backend_unavailable") from exc

        retry_after = ttl if ttl > 0 else window_seconds
        return RateLimitDecision(
            allowed=current <= limit,
            retry_after_seconds=max(retry_after, 1),
        )


def _as_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, bytes):
        return int(value.decode("ascii"))
    if isinstance(value, str):
        return int(value)
    raise TypeError("rate_limit_result_not_integer")
