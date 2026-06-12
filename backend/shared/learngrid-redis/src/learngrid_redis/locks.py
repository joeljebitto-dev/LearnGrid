from __future__ import annotations

import uuid
from dataclasses import dataclass

import redis


_RELEASE_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
end
return 0
"""


class RedisLockNotAcquired(RuntimeError):
    pass


@dataclass
class RedisLock:
    client: redis.Redis
    key: str
    ttl_seconds: int
    token: str
    acquired: bool = False

    def acquire(self) -> bool:
        try:
            self.acquired = bool(
                self.client.set(
                    self.key,
                    self.token,
                    nx=True,
                    ex=max(1, self.ttl_seconds),
                )
            )
        except (redis.RedisError, OSError):
            self.acquired = False
        return self.acquired

    def release(self) -> bool:
        if not self.acquired:
            return False
        try:
            released = bool(self.client.eval(_RELEASE_SCRIPT, 1, self.key, self.token))
        except (redis.RedisError, OSError):
            return False
        finally:
            self.acquired = False
        return released

    def __enter__(self) -> "RedisLock":
        if not self.acquire():
            raise RedisLockNotAcquired(f"Redis lock was not acquired: {self.key}")
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        self.release()


def redis_lock(client: redis.Redis, key: str, ttl_seconds: int) -> RedisLock:
    return RedisLock(
        client=client,
        key=key,
        ttl_seconds=ttl_seconds,
        token=str(uuid.uuid4()),
    )
