from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


class EventValidationError(ValueError):
    pass


@dataclass(frozen=True)
class EventEnvelope:
    event_id: str
    event_type: str
    aggregate_id: str
    producer_service: str
    timestamp: str
    version: int
    correlation_id: str | None
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def create_event_envelope(
    *,
    event_type: str,
    aggregate_id,
    producer_service: str,
    payload: dict[str, Any] | None = None,
    correlation_id: str | None = None,
    event_id: str | None = None,
    timestamp: datetime | str | None = None,
    version: int = 1,
) -> EventEnvelope:
    raw_timestamp = timestamp or datetime.now(UTC)
    timestamp_value = (
        raw_timestamp.isoformat()
        if isinstance(raw_timestamp, datetime)
        else str(raw_timestamp)
    )
    envelope = EventEnvelope(
        event_id=str(event_id or uuid.uuid4()),
        event_type=event_type,
        aggregate_id=str(aggregate_id),
        producer_service=producer_service,
        timestamp=timestamp_value,
        version=version,
        correlation_id=str(correlation_id) if correlation_id else None,
        payload=payload or {},
    )
    validate_event_envelope(envelope.to_dict())
    return envelope


def validate_event_envelope(data: dict[str, Any]) -> dict[str, Any]:
    required_fields = [
        "event_id",
        "event_type",
        "aggregate_id",
        "producer_service",
        "timestamp",
        "version",
        "correlation_id",
        "payload",
    ]
    for field in required_fields:
        if field not in data:
            raise EventValidationError(f"Missing event envelope field: {field}")

    _require_uuid("event_id", data["event_id"])
    _require_uuid("aggregate_id", data["aggregate_id"])
    if data.get("correlation_id"):
        _require_uuid("correlation_id", data["correlation_id"])

    for field in ["event_type", "producer_service", "timestamp"]:
        if not isinstance(data[field], str) or not data[field].strip():
            raise EventValidationError(f"Invalid event envelope field: {field}")

    if not isinstance(data["version"], int) or data["version"] < 1:
        raise EventValidationError("Event envelope version must be a positive integer.")
    if not isinstance(data["payload"], dict):
        raise EventValidationError("Event envelope payload must be an object.")
    _parse_timestamp(data["timestamp"])
    return data


def _require_uuid(field: str, value) -> None:
    try:
        uuid.UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise EventValidationError(f"Event envelope field {field} must be a UUID.") from exc


def _parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise EventValidationError("Event envelope timestamp must be ISO-8601.") from exc
