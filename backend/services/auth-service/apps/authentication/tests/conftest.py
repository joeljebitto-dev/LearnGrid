from __future__ import annotations

import pytest

from apps.authentication import services


class FakeRedis:
    def __init__(self):
        self.data: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    def get(self, key):
        return self.data.get(key)

    def setex(self, key, ttl, value):
        self.data[key] = value
        self.ttls[key] = ttl

    def exists(self, key):
        return int(key in self.data)

    def scan_iter(self, pattern):
        prefix = pattern.removesuffix("*")
        return [key for key in self.data if key.startswith(prefix)]

    def delete(self, *keys):
        deleted = 0
        for key in keys:
            if key in self.data:
                deleted += 1
            self.data.pop(key, None)
            self.ttls.pop(key, None)
        return deleted

    def incr(self, key):
        self.data[key] = str(int(self.data.get(key, "0")) + 1)
        return int(self.data[key])

    def expire(self, key, ttl):
        self.ttls[key] = ttl

    def ttl(self, key):
        return self.ttls.get(key, -1)


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    client = FakeRedis()
    monkeypatch.setattr(services, "_redis_client", lambda: client)
    return client
