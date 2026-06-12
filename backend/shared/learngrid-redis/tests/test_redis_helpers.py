from __future__ import annotations

import json

import pytest
import redis

import learngrid_redis.client as redis_client_module
from learngrid_redis import (
    RedisKeyBuilder,
    RedisLockNotAcquired,
    digest_json,
    fixed_window_rate_limit,
    get_json_cache,
    redis_client,
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


class FakeSentinel:
    calls = []

    def __init__(self, sentinels, **kwargs):
        self.sentinels = sentinels
        self.kwargs = kwargs
        FakeSentinel.calls.append(("init", sentinels, kwargs))

    def master_for(self, master_name, **kwargs):
        FakeSentinel.calls.append(("master_for", master_name, kwargs))
        return {"master_name": master_name, "kwargs": kwargs}


def test_key_builder_normalizes_parts_and_hashes_sensitive_suffixes():
    builder = RedisKeyBuilder(service="auth-service", env="local")
    suffix = digest_json({"email": "USER@example.com", "ip": "127.0.0.1"})

    key = builder.key("rate-limit", "login", suffix)

    assert key.startswith("lg:local:auth-service:rate-limit:login:")
    assert "USER@example.com" not in key
    assert "127.0.0.1" not in key
    assert len(suffix) == 64


def test_redis_client_uses_direct_url_by_default(monkeypatch):
    calls = []

    class FakeRedisFactory:
        @staticmethod
        def from_url(redis_url, **kwargs):
            calls.append((redis_url, kwargs))
            return {"redis_url": redis_url, "kwargs": kwargs}

    monkeypatch.setattr(redis_client_module.redis, "Redis", FakeRedisFactory)

    client = redis_client("redis://localhost:6379/2")

    assert client["redis_url"] == "redis://localhost:6379/2"
    assert calls[0][1]["decode_responses"] is True


def test_redis_client_uses_sentinel_when_configured(monkeypatch):
    FakeSentinel.calls = []
    monkeypatch.setattr(redis_client_module, "Sentinel", FakeSentinel)

    client = redis_client(
        "redis://redis:6379/4",
        sentinel_urls="redis://sentinel-a:26379,sentinel-b:26380",
        sentinel_master_name="mymaster",
        sentinel_password="sentinel-secret",
        password="redis-secret",
        decode_responses=False,
    )

    assert client["master_name"] == "mymaster"
    assert FakeSentinel.calls[0] == (
        "init",
        [("sentinel-a", 26379), ("sentinel-b", 26380)],
        {
            "socket_connect_timeout": 0.2,
            "socket_timeout": 0.2,
            "sentinel_kwargs": {"password": "sentinel-secret"},
        },
    )
    assert FakeSentinel.calls[1][2] == {
        "db": 4,
        "password": "redis-secret",
        "decode_responses": False,
        "socket_connect_timeout": 0.2,
        "socket_timeout": 0.2,
    }


def test_redis_client_sentinel_uses_password_from_redis_url(monkeypatch):
    FakeSentinel.calls = []
    monkeypatch.setattr(redis_client_module, "Sentinel", FakeSentinel)

    redis_client(
        "redis://:url-secret@redis:6379/0",
        sentinel_urls="sentinel-a:26379",
    )

    assert FakeSentinel.calls[1][2]["password"] == "url-secret"


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
