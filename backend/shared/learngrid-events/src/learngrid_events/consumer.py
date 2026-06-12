from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .adapters import decode_headers, encode_headers
from .envelope import validate_event_envelope
from .topics import dead_letter_topic, retry_topic


class DuplicateEvent(Exception):
    pass


class RetryableEventError(Exception):
    pass


class DeadLetterEventError(Exception):
    pass


@dataclass(frozen=True)
class ConsumerResult:
    status: str
    event_id: str
    attempts: int = 0
    error: str | None = None


def consume_event(
    *,
    topic: str,
    event: dict[str, Any],
    handler: Callable[[dict[str, Any]], Any],
    adapter,
    headers: dict[str, Any] | list[tuple[str, bytes]] | None = None,
    max_retry_attempts: int = 3,
) -> ConsumerResult:
    validate_event_envelope(event)
    decoded_headers = decode_headers(headers) if isinstance(headers, (list, tuple)) else {**(headers or {})}
    attempts = int(decoded_headers.get("x-retry-attempt", "0"))
    try:
        handler(event)
    except DuplicateEvent:
        return ConsumerResult(status="duplicate", event_id=event["event_id"], attempts=attempts)
    except DeadLetterEventError as exc:
        _send_dead_letter(adapter=adapter, topic=topic, event=event, attempts=attempts, error=exc)
        return ConsumerResult(
            status="dead_lettered",
            event_id=event["event_id"],
            attempts=attempts,
            error=str(exc),
        )
    except Exception as exc:
        if attempts + 1 >= max_retry_attempts:
            _send_dead_letter(adapter=adapter, topic=topic, event=event, attempts=attempts + 1, error=exc)
            return ConsumerResult(
                status="dead_lettered",
                event_id=event["event_id"],
                attempts=attempts + 1,
                error=str(exc),
            )
        adapter.send(
            retry_topic(topic),
            event,
            key=event["aggregate_id"],
            headers=encode_headers(
                {
                    "x-retry-attempt": attempts + 1,
                    "x-original-topic": topic,
                    "x-error": str(exc),
                }
            ),
        )
        return ConsumerResult(
            status="retry_scheduled",
            event_id=event["event_id"],
            attempts=attempts + 1,
            error=str(exc),
        )
    return ConsumerResult(status="processed", event_id=event["event_id"], attempts=attempts)


def _send_dead_letter(*, adapter, topic: str, event: dict[str, Any], attempts: int, error: Exception) -> None:
    adapter.send(
        dead_letter_topic(topic),
        event,
        key=event["aggregate_id"],
        headers=encode_headers(
            {
                "x-retry-attempt": attempts,
                "x-original-topic": topic,
                "x-error": str(error),
            }
        ),
    )
