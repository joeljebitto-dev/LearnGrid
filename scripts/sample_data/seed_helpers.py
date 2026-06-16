from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.core.management.base import CommandError
from django.utils import timezone


SEED_NAMESPACE = "learngrid-demo"


def repo_root(command_file: str) -> Path:
    return Path(command_file).resolve().parents[7]


def default_manifest(command_file: str) -> Path:
    return repo_root(command_file) / "scripts" / "sample-data" / "learngrid-demo.json"


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise CommandError(f"Sample data manifest does not exist: {manifest_path}")
    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if manifest.get("seed_namespace") != SEED_NAMESPACE:
        raise CommandError(
            f"Unsupported seed namespace {manifest.get('seed_namespace')!r}; "
            f"expected {SEED_NAMESPACE!r}."
        )
    return manifest


def add_seed_arguments(parser, command_file: str) -> None:
    parser.add_argument("--manifest", default=str(default_manifest(command_file)))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reset-sample-data", action="store_true")


def planned(command, service: str, manifest: dict[str, Any], records: list[str]) -> None:
    command.stdout.write(
        json.dumps(
            {
                "service": service,
                "seed_namespace": manifest["seed_namespace"],
                "records": records,
            },
            indent=2,
        )
    )


def seed_metadata(seed_key: str, **extra: Any) -> dict[str, Any]:
    metadata = {"seed_namespace": SEED_NAMESPACE, "seed_key": seed_key}
    metadata.update(extra)
    return metadata


def uuid_value(value: str | uuid.UUID | None) -> uuid.UUID | None:
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def decimal_value(value: str | int | float) -> Decimal:
    return Decimal(str(value))


def now():
    return timezone.now()


def today() -> date:
    return timezone.localdate()


def days_from_now(days: int) -> datetime:
    return now() + timedelta(days=days)


def utc_datetime(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=dt_timezone.utc)


def profile_id(manifest: dict[str, Any], key: str) -> uuid.UUID:
    return uuid_value(manifest["accounts"][key]["profile_id"])


def account_id(manifest: dict[str, Any], key: str) -> uuid.UUID:
    return uuid_value(manifest["accounts"][key]["id"])


def institution_id(manifest: dict[str, Any]) -> uuid.UUID:
    return uuid_value(manifest["institution"]["id"])


def course_id(manifest: dict[str, Any], key: str = "main") -> uuid.UUID:
    return uuid_value(manifest["courses"][key]["id"])

