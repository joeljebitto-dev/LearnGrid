from __future__ import annotations

import json

import pytest
import redis

from learngrid_redis import (
    RedisKeyBuilder,
    RedisLockNotAcquired,
    digest_json,
    fixed_window_rate_limit,
    get_json_cache,
    redis_lock,
    set_json_cache,
)


class FakeRedis:
    def __init__(self):
        self.store = {}
        self.ttls = {}
        self.deleted = []

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, value):
        self.store[key] = value
        self.ttls[key] = ttl

    def incr(self, key):
        self.store[key] = str(int(self.store.get(key, "0")) + 1)
        return int(self.store[key])

    def expire(self, key, ttl):
        self.ttls[key] = ttl

    def ttl(self, key):
        return self.ttls.get(key, -1)

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.store:
            return False
        self.store[key] = value
        self.ttls[key] = ex
        return True

    def eval(self, _script, _count, key, token):
        if self.store.get(key) == token:
            self.deleted.append(key)
            self.store.pop(key, None)
            return 1
        return 0


class BrokenRedis:
    def get(self, _key):
        raise redis.RedisError("unavailable")

    def setex(self, *_args):
        raise redis.RedisError("unavailable")

    def incr(self, _key):
        raise redis.RedisError("unavailable")

    def set(self, *_args, **_kwargs):
        raise redis.RedisError("unavailable")


def test_key_builder_normalizes_parts_and_hashes_sensitive_suffixes():
    builder = RedisKeyBuilder(service="auth-service", env="local")
    suffix = digest_json({"email": "USER@example.com", "ip": "127.0.0.1"})

    key = builder.key("rate-limit", "login", suffix)

    assert key.startswith("lg:local:auth-service:rate-limit:login:")
    assert "USER@example.com" not in key
    assert "127.0.0.1" not in key
    assert len(suffix) == 64


def test_json_cache_round_trips_with_ttl():
    client = FakeRedis()

    assert set_json_cache(client, "cache-key", {"count": 2}, ttl_seconds=30)
    assert json.loads(client.store["cache-key"]) == {"count": 2}
    assert client.ttls["cache-key"] == 30
    assert get_json_cache(client, "cache-key") == {"count": 2}


def test_json_cache_miss_and_outage_return_none():
    assert get_json_cache(FakeRedis(), "missing") is None
    assert get_json_cache(BrokenRedis(), "missing") is None
    assert not set_json_cache(BrokenRedis(), "cache-key", {"count": 2}, ttl_seconds=30)


def test_fixed_window_rate_limit_sets_ttl_and_blocks_after_limit():
    client = FakeRedis()

    first = fixed_window_rate_limit(client, "limit-key", limit=2, window_seconds=60)
    second = fixed_window_rate_limit(client, "limit-key", limit=2, window_seconds=60)
    third = fixed_window_rate_limit(client, "limit-key", limit=2, window_seconds=60)

    assert first.allowed
    assert second.allowed
    assert not third.allowed
    assert client.ttls["limit-key"] == 60


def test_fixed_window_rate_limit_fails_closed_when_redis_fails():
    with pytest.raises(RuntimeError):
        fixed_window_rate_limit(BrokenRedis(), "limit-key", limit=2, window_seconds=60)


def test_redis_lock_releases_only_owned_lock():
    client = FakeRedis()
    lock = redis_lock(client, "lock-key", ttl_seconds=10)

    with lock:
        assert client.store["lock-key"] == lock.token

    assert "lock-key" not in client.store
    assert client.deleted == ["lock-key"]


def test_redis_lock_raises_when_not_acquired():
    client = FakeRedis()
    client.store["lock-key"] = "someone-else"

    with pytest.raises(RedisLockNotAcquired):
        with redis_lock(client, "lock-key", ttl_seconds=10):
            pass
