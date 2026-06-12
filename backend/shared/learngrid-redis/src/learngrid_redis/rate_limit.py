from __future__ import annotations

from dataclasses import dataclass

import redis


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    count: int
    limit: int
    ttl_seconds: int


def fixed_window_rate_limit(
    client: redis.Redis,
    key: str,
    *,
    limit: int,
    window_seconds: int,
) -> RateLimitResult:
    if limit <= 0 or window_seconds <= 0:
        return RateLimitResult(allowed=False, count=0, limit=limit, ttl_seconds=0)
    try:
        count = int(client.incr(key))
        if count == 1:
            client.expire(key, window_seconds)
        ttl = int(client.ttl(key))
    except (redis.RedisError, OSError) as exc:
        raise RuntimeError("Redis rate limiter is unavailable.") from exc
    return RateLimitResult(
        allowed=count <= limit,
        count=count,
        limit=limit,
        ttl_seconds=max(0, ttl),
    )
