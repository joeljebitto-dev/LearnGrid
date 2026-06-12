from __future__ import annotations

import pytest

from apps.analytics import services


class FakeRedis:
    def __init__(self):
        self.data: dict[str, str] = {}
        self.ttls: dict[str, int] = {}
        self.delete_count = 0
        self.set_count = 0

    def get(self, key):
        return self.data.get(key)

    def setex(self, key, ttl, value):
        self.data[key] = value
        self.ttls[key] = ttl
        self.set_count += 1

    def scan_iter(self, pattern):
        prefix = pattern.removesuffix("*")
        return [key for key in self.data if key.startswith(prefix)]

    def delete(self, key):
        self.delete_count += 1
        self.data.pop(key, None)
        self.ttls.pop(key, None)


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    client = FakeRedis()
    monkeypatch.setattr(services, "_redis_client", lambda: client)
    return client
