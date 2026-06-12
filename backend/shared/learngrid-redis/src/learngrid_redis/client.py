from __future__ import annotations

from urllib.parse import urlparse

import redis
from redis.sentinel import Sentinel


def _parse_sentinel_urls(sentinel_urls: str) -> list[tuple[str, int]]:
    hosts: list[tuple[str, int]] = []
    for raw_url in sentinel_urls.split(","):
        value = raw_url.strip()
        if not value:
            continue
        parsed = urlparse(value if "://" in value else f"redis://{value}")
        if not parsed.hostname:
            raise ValueError(f"Invalid Redis Sentinel URL: {value}")
        hosts.append((parsed.hostname, parsed.port or 26379))
    if not hosts:
        raise ValueError("At least one Redis Sentinel URL is required.")
    return hosts


def _database_number(redis_url: str) -> int:
    parsed = urlparse(redis_url)
    if not parsed.path or parsed.path == "/":
        return 0
    return int(parsed.path.lstrip("/"))


def _password_from_url(redis_url: str) -> str | None:
    return urlparse(redis_url).password


def redis_client(
    redis_url: str,
    *,
    decode_responses: bool = True,
    socket_connect_timeout: float = 0.2,
    socket_timeout: float = 0.2,
    sentinel_urls: str | None = None,
    sentinel_master_name: str = "mymaster",
    sentinel_password: str | None = None,
    password: str | None = None,
) -> redis.Redis:
    if sentinel_urls:
        sentinel_kwargs = {"password": sentinel_password} if sentinel_password else None
        sentinel = Sentinel(
            _parse_sentinel_urls(sentinel_urls),
            socket_connect_timeout=socket_connect_timeout,
            socket_timeout=socket_timeout,
            sentinel_kwargs=sentinel_kwargs,
        )
        return sentinel.master_for(
            sentinel_master_name,
            db=_database_number(redis_url),
            password=password if password is not None else _password_from_url(redis_url),
            decode_responses=decode_responses,
            socket_connect_timeout=socket_connect_timeout,
            socket_timeout=socket_timeout,
        )

    return redis.Redis.from_url(
        redis_url,
        decode_responses=decode_responses,
        socket_connect_timeout=socket_connect_timeout,
        socket_timeout=socket_timeout,
    )
