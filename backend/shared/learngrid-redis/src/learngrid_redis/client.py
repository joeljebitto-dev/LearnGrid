from __future__ import annotations

import redis


def redis_client(
    redis_url: str,
    *,
    decode_responses: bool = True,
    socket_connect_timeout: float = 0.2,
    socket_timeout: float = 0.2,
) -> redis.Redis:
    return redis.Redis.from_url(
        redis_url,
        decode_responses=decode_responses,
        socket_connect_timeout=socket_connect_timeout,
        socket_timeout=socket_timeout,
    )
