from __future__ import annotations

from uuid import uuid4

import pytest
from django.conf import settings

from learngrid_events.adapters import FakeKafkaAdapter
from learngrid_events.consumer import DuplicateEvent, consume_event
from learngrid_events.envelope import (
    EventValidationError,
    create_event_envelope,
    validate_event_envelope,
)
from learngrid_events.producer import publish_event
from learngrid_events.topics import BASE_TOPICS, DEAD_LETTER_TOPICS, RETRY_TOPICS, TopicName


def configure_django_settings(**overrides):
    if not settings.configured:
        settings.configure(
            SERVICE_NAME="course-service",
            KAFKA_ENABLED=False,
            KAFKA_BOOTSTRAP_SERVERS="127.0.0.1:9092",
            KAFKA_CLIENT_ID="test-client",
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    for key, value in overrides.items():
        setattr(settings, key, value)


def raise_runtime_error(message: str):
    def handler(_event):
        raise RuntimeError(message)

    return handler


def test_event_envelope_validation_accepts_spec_fields():
    event = create_event_envelope(
        event_type="CoursePublished",
        aggregate_id=uuid4(),
        producer_service="course-service",
        correlation_id=str(uuid4()),
        payload={"status": "published"},
    )

    assert validate_event_envelope(event.to_dict())["event_type"] == "CoursePublished"
    assert event.version == 1


def test_event_envelope_validation_rejects_missing_fields():
    with pytest.raises(EventValidationError):
        validate_event_envelope({"event_id": str(uuid4())})


def test_topic_catalog_contains_base_retry_and_dead_letter_topics():
    assert TopicName.COURSE.value in BASE_TOPICS
    assert "course.events.retry" in RETRY_TOPICS
    assert "course.events.dlq" in DEAD_LETTER_TOPICS
    assert len(BASE_TOPICS) == 10


def test_publish_event_uses_configured_topic_when_kafka_enabled():
    configure_django_settings(KAFKA_ENABLED=True, SERVICE_NAME="course-service")
    adapter = FakeKafkaAdapter()

    event = publish_event(
        event_type="CoursePublished",
        aggregate_id=uuid4(),
        payload={"status": "published"},
        adapter=adapter,
        on_commit=False,
    )

    assert event["producer_service"] == "course-service"
    assert adapter.messages[0].topic == "course.events"
    assert adapter.messages[0].value["event_id"] == event["event_id"]


def test_consumer_processes_successful_event():
    event = create_event_envelope(
        event_type="CoursePublished",
        aggregate_id=uuid4(),
        producer_service="course-service",
        payload={},
    ).to_dict()
    result = consume_event(
        topic="course.events",
        event=event,
        handler=lambda _event: None,
        adapter=FakeKafkaAdapter(),
    )

    assert result.status == "processed"


def test_consumer_marks_duplicate_without_retry():
    event = create_event_envelope(
        event_type="CoursePublished",
        aggregate_id=uuid4(),
        producer_service="course-service",
        payload={},
    ).to_dict()

    def handler(_event):
        raise DuplicateEvent()

    adapter = FakeKafkaAdapter()
    result = consume_event(topic="course.events", event=event, handler=handler, adapter=adapter)

    assert result.status == "duplicate"
    assert adapter.messages == []


def test_consumer_retries_then_dead_letters():
    event = create_event_envelope(
        event_type="CoursePublished",
        aggregate_id=uuid4(),
        producer_service="course-service",
        payload={},
    ).to_dict()
    adapter = FakeKafkaAdapter()

    first = consume_event(
        topic="course.events",
        event=event,
        handler=raise_runtime_error("temporary"),
        adapter=adapter,
        max_retry_attempts=2,
    )
    second = consume_event(
        topic="course.events",
        event=event,
        handler=raise_runtime_error("poison"),
        adapter=adapter,
        headers={"x-retry-attempt": "1"},
        max_retry_attempts=2,
    )

    assert first.status == "retry_scheduled"
    assert adapter.messages[0].topic == "course.events.retry"
    assert second.status == "dead_lettered"
    assert adapter.messages[1].topic == "course.events.dlq"
