from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable


_SAFE_PART = re.compile(r"[^a-zA-Z0-9_.-]+")


def _normalize_part(value: str) -> str:
    normalized = _SAFE_PART.sub("-", str(value).strip()).strip("-").lower()
    return normalized or "none"


def digest_value(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def digest_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return digest_value(payload)


@dataclass(frozen=True)
class RedisKeyBuilder:
    service: str
    env: str = "local"
    prefix: str = "lg"

    def key(
        self,
        workload: str,
        name: str,
        suffix: str | Iterable[str] | None = None,
    ) -> str:
        parts = [
            self.prefix,
            self.env,
            self.service,
            workload,
            name,
        ]
        if suffix is not None:
            if isinstance(suffix, str):
                parts.append(suffix)
            else:
                parts.extend(suffix)
        return ":".join(_normalize_part(part) for part in parts)

    def prefix_for(
        self, workload: str, name: str, suffix: str | Iterable[str] | None = None
    ) -> str:
        return f"{self.key(workload, name, suffix)}:"
