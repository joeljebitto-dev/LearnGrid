from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import jwt
import pytest
from django.conf import settings
from django.utils import timezone
from learngrid_events import DuplicateEvent
from rest_framework.test import APIClient

from apps.progress import permissions, services
from apps.progress.models import CourseProgressStatus, ProgressEvent


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def access_token():
    now = timezone.now()
    return jwt.encode(
        {
            "iss": settings.AUTH_JWT_ISSUER,
            "sub": str(uuid4()),
            "typ": "access",
            "jti": str(uuid4()),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
        settings.AUTH_JWT_SIGNING_KEY,
        algorithm=settings.AUTH_JWT_ALGORITHM,
    )


def auth_headers(token: str) -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def allow_progress(monkeypatch, course_id):
    monkeypatch.setattr(
        permissions,
        "remote_authorization_check",
        lambda **kwargs: (
            kwargs["permission"] in {"progress.manage", "progress.view"}
            and kwargs["scope_type"] == "course"
            and kwargs["scope_id"] == str(course_id)
        )
        or (
            kwargs["permission"] == "progress.view"
            and kwargs["scope_type"] == "platform"
            and kwargs["scope_id"] is None
        ),
    )


@pytest.mark.django_db
def test_progress_updates_course_completion_and_events(api_client, access_token, monkeypatch):
    course_id = uuid4()
    student_id = uuid4()
    allow_progress(monkeypatch, course_id)
    events = []
    monkeypatch.setattr(
        services,
        "publish_progress_event",
        lambda **kwargs: events.append(kwargs) or {"event_id": "evt"},
    )

    response = api_client.post(
        "/api/progress/lessons/",
        {
            "student_profile_id": str(student_id),
            "course_id": str(course_id),
            "lesson_id": str(uuid4()),
            "status": "completed",
            "total_lessons": 1,
            "total_assessments": 1,
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert events[-1]["event_type"] == "CourseProgressUpdated"

    response = api_client.post(
        "/api/progress/assessments/",
        {
            "student_profile_id": str(student_id),
            "course_id": str(course_id),
            "assessment_id": str(uuid4()),
            "status": "submitted",
            "total_lessons": 1,
            "total_assessments": 1,
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 200
    assert events[-1]["event_type"] == "CourseCompleted"

    response = api_client.get(
        "/api/progress/courses/",
        {"student_profile_id": str(student_id), "course_id": str(course_id)},
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert response.json()["results"][0]["status"] == CourseProgressStatus.COMPLETED
    assert response.json()["results"][0]["completion_percent"] == "100.00"


@pytest.mark.django_db
def test_event_ingestion_is_idempotent(api_client, access_token, monkeypatch):
    course_id = uuid4()
    student_id = uuid4()
    event_id = uuid4()
    allow_progress(monkeypatch, course_id)

    payload = {
        "student_profile_id": str(student_id),
        "course_id": str(course_id),
        "lesson_id": str(uuid4()),
        "total_lessons": 1,
    }
    response = api_client.post(
        "/api/progress/events/",
        {
            "event_id": str(event_id),
            "event_type": "LessonViewed",
            "aggregate_id": str(payload["lesson_id"]),
            "payload": payload,
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["status"] == "processed"

    response = api_client.post(
        "/api/progress/events/",
        {
            "event_id": str(event_id),
            "event_type": "LessonViewed",
            "aggregate_id": str(payload["lesson_id"]),
            "payload": payload,
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["status"] == "duplicate"
    assert ProgressEvent.objects.count() == 1


@pytest.mark.django_db
def test_kafka_progress_handler_processes_assessment_event_idempotently(monkeypatch):
    course_id = uuid4()
    student_id = uuid4()
    event = {
        "event_id": str(uuid4()),
        "event_type": "QuizSubmitted",
        "aggregate_id": str(uuid4()),
        "producer_service": "assessment-service",
        "timestamp": timezone.now().isoformat(),
        "payload": {
            "student_profile_id": str(student_id),
            "course_id": str(course_id),
            "assessment_id": str(uuid4()),
        },
    }
    published_events = []
    monkeypatch.setattr(
        services,
        "publish_progress_event",
        lambda **kwargs: published_events.append(kwargs) or {"event_id": str(uuid4())},
    )

    result = services.handle_kafka_progress_event(event)

    assert result["status"] == "processed"
    assert ProgressEvent.objects.filter(event_id=event["event_id"]).exists()
    assert published_events[-1]["event_type"] == "CourseCompleted"
    with pytest.raises(DuplicateEvent):
        services.handle_kafka_progress_event(event)


@pytest.mark.django_db
def test_progress_permission_denial(api_client, access_token, monkeypatch):
    monkeypatch.setattr(permissions, "remote_authorization_check", lambda **_kwargs: False)
    response = api_client.post(
        "/api/progress/videos/",
        {
            "student_profile_id": str(uuid4()),
            "course_id": str(uuid4()),
            "content_asset_id": str(uuid4()),
            "duration_seconds": 100,
            "last_position_seconds": 100,
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 403
