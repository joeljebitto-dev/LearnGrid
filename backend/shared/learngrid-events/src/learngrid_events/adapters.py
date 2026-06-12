from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


HeaderList = list[tuple[str, bytes]]


@dataclass
class PublishedMessage:
    topic: str
    value: dict[str, Any]
    key: str | None = None
    headers: HeaderList = field(default_factory=list)


class FakeKafkaAdapter:
    def __init__(self) -> None:
        self.messages: list[PublishedMessage] = []

    def send(
        self,
        topic: str,
        value: dict[str, Any],
        *,
        key: str | None = None,
        headers: HeaderList | None = None,
    ) -> PublishedMessage:
        message = PublishedMessage(topic=topic, value=value, key=key, headers=headers or [])
        self.messages.append(message)
        return message

    def flush(self) -> None:
        return None

    def close(self) -> None:
        return None


class KafkaProducerAdapter:
    def __init__(self, *, bootstrap_servers: str, client_id: str) -> None:
        from kafka import KafkaProducer

        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers.split(","),
            client_id=client_id,
            key_serializer=lambda value: value.encode("utf-8") if value else None,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )

    def send(
        self,
        topic: str,
        value: dict[str, Any],
        *,
        key: str | None = None,
        headers: HeaderList | None = None,
    ):
        result = self.producer.send(topic, key=key, value=value, headers=headers or [])
        self.producer.flush()
        return result

    def flush(self) -> None:
        self.producer.flush()

    def close(self) -> None:
        self.producer.close()


def encode_headers(headers: dict[str, Any] | None = None) -> HeaderList:
    encoded = []
    for key, value in (headers or {}).items():
        encoded.append((key, str(value).encode("utf-8")))
    return encoded


def decode_headers(
    headers: HeaderList | tuple[tuple[str, bytes], ...] | None = None,
) -> dict[str, str]:
    decoded = {}
    for key, value in headers or []:
        decoded[key] = value.decode("utf-8") if isinstance(value, bytes) else str(value)
    return decoded
