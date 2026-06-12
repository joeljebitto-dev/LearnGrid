from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "shared" / "learngrid-events" / "src"))

from learngrid_events.envelope import create_event_envelope, validate_event_envelope  # noqa: E402
from learngrid_events.topics import (  # noqa: E402
    BASE_TOPICS,
    DEAD_LETTER_TOPICS,
    RETRY_TOPICS,
    TOPIC_BY_SERVICE,
    dead_letter_topic,
    retry_topic,
)


EXPECTED_SERVICE_TOPICS = {
    "auth-service": "audit.events",
    "user-service": "user.events",
    "course-service": "course.events",
    "content-service": "content.events",
    "enrollment-service": "enrollment.events",
    "progress-service": "progress.events",
    "assessment-service": "assessment.events",
    "grading-service": "grading.events",
    "notification-service": "notification.events",
    "analytics-service": "analytics.events",
}

REPRESENTATIVE_EVENTS = [
    ("CoursePublished", "course-service", {"course_id": str(uuid4()), "status": "published"}),
    ("LessonViewed", "progress-service", {"lesson_id": str(uuid4()), "seconds": 30}),
    ("QuizSubmitted", "assessment-service", {"attempt_id": str(uuid4()), "score": 8}),
    ("GradePublished", "grading-service", {"grade_record_id": str(uuid4()), "score": 92}),
    ("NotificationCreated", "notification-service", {"notification_id": str(uuid4())}),
    ("AnalyticsEventIngested", "analytics-service", {"event_type": "dashboard.viewed"}),
]


def test_service_topic_contract_is_stable():
    assert TOPIC_BY_SERVICE == EXPECTED_SERVICE_TOPICS
    assert len(BASE_TOPICS) == len(EXPECTED_SERVICE_TOPICS)
    for topic in BASE_TOPICS:
        assert retry_topic(topic) in RETRY_TOPICS
        assert dead_letter_topic(topic) in DEAD_LETTER_TOPICS


def test_representative_events_match_envelope_contract():
    for event_type, producer_service, payload in REPRESENTATIVE_EVENTS:
        event = create_event_envelope(
            event_type=event_type,
            aggregate_id=uuid4(),
            producer_service=producer_service,
            payload=payload,
        ).to_dict()
        assert validate_event_envelope(event) == event
        assert event["version"] == 1
        assert event["producer_service"] == producer_service
        assert event["payload"] == payload
