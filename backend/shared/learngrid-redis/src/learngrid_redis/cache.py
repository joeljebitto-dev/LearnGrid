from __future__ import annotations

import json
from typing import Any

import redis


def get_json_cache(client: redis.Redis, key: str) -> Any | None:
    try:
        cached = client.get(key)
    except (redis.RedisError, OSError):
        return None
    if not cached:
        return None
    try:
        return json.loads(cached)
    except (TypeError, ValueError):
        return None


def set_json_cache(client: redis.Redis, key: str, value: Any, ttl_seconds: int) -> bool:
    if ttl_seconds <= 0:
        return False
    try:
        client.setex(key, ttl_seconds, json.dumps(value, sort_keys=True, default=str))
    except (redis.RedisError, OSError, TypeError, ValueError):
        return False
    return True
