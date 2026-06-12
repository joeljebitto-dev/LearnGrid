from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.db import transaction

from .adapters import KafkaProducerAdapter, encode_headers
from .envelope import create_event_envelope
from .topics import TOPIC_BY_SERVICE


logger = logging.getLogger(__name__)


def publish_event(
    *,
    event_type: str,
    aggregate_id,
    payload: dict[str, Any] | None = None,
    correlation_id: str | None = None,
    producer_service: str | None = None,
    topic: str | None = None,
    adapter=None,
    on_commit: bool = True,
) -> dict[str, Any]:
    service_name = producer_service or getattr(settings, "SERVICE_NAME", "unknown-service")
    event = create_event_envelope(
        event_type=event_type,
        aggregate_id=aggregate_id,
        producer_service=service_name,
        correlation_id=correlation_id,
        payload=payload or {},
    ).to_dict()
    selected_topic = topic or TOPIC_BY_SERVICE.get(service_name)
    if not selected_topic:
        raise ValueError(f"No Kafka topic configured for service {service_name}.")

    def send() -> None:
        if not kafka_enabled():
            logger.info(
                "kafka_event_local topic=%s event_id=%s event_type=%s",
                selected_topic,
                event["event_id"],
                event["event_type"],
            )
            return
        producer = adapter or default_producer_adapter(service_name=service_name)
        producer.send(
            selected_topic,
            event,
            key=str(aggregate_id),
            headers=encode_headers({"event_type": event_type, "producer_service": service_name}),
        )

    if on_commit:
        transaction.on_commit(send)
    else:
        send()
    return event


def kafka_enabled() -> bool:
    value = getattr(settings, "KAFKA_ENABLED", False)
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return bool(value)


def default_producer_adapter(*, service_name: str):
    return KafkaProducerAdapter(
        bootstrap_servers=getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092"),
        client_id=getattr(settings, "KAFKA_CLIENT_ID", service_name),
    )
