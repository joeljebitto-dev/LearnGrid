from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import jwt
import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.notifications import permissions, views
from apps.notifications.models import (
    DeliveryAttempt,
    DeliveryStatus,
    Notification,
    NotificationChannel,
    NotificationTemplate,
    UserNotificationPreference,
)


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


def allow_notification_permissions(monkeypatch, allowed=None):
    if allowed is None:
        allowed = {"notification.view", "notification.manage"}

    def fake_remote_authorization_check(**kwargs):
        return kwargs["permission"] in allowed

    monkeypatch.setattr(permissions, "remote_authorization_check", fake_remote_authorization_check)


def patch_profile(monkeypatch, profile_id, profile_type="student"):
    monkeypatch.setattr(
        views,
        "current_profile",
        lambda **_kwargs: {"id": str(profile_id), "profile_type": profile_type},
    )


def event_payload(event_type: str, student_id, **payload):
    return {
        "event_id": str(uuid4()),
        "event_type": event_type,
        "aggregate_id": str(uuid4()),
        "producer_service": "test-service",
        "payload": {
            "student_profile_id": str(student_id),
            "course_id": str(uuid4()),
            "course_title": "Physics 101",
            "assignment_title": "Lab report",
            "assessment_title": "Midterm",
            "due_at": "2026-06-09T10:00:00Z",
            **payload,
        },
    }


@pytest.mark.django_db
def test_template_crud(api_client, access_token, monkeypatch):
    allow_notification_permissions(monkeypatch)

    create_response = api_client.post(
        "/api/notifications/templates/",
        {
            "event_type": "GradePublished",
            "channel": "in_app",
            "subject_template": "Grade ready",
            "body_template": "Grade for {assessment_title} is ready.",
        },
        **auth_headers(access_token),
        format="json",
    )
    assert create_response.status_code == 201
    template_id = create_response.json()["id"]

    update_response = api_client.patch(
        f"/api/notifications/templates/{template_id}/",
        {"status": "inactive"},
        **auth_headers(access_token),
        format="json",
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "inactive"


@pytest.mark.django_db
@pytest.mark.parametrize("event_type", ["StudentEnrolled", "AssignmentDueSoon", "GradePublished", "CourseCompleted"])
def test_event_ingestion_creates_in_app_notification(api_client, access_token, monkeypatch, event_type):
    student_id = uuid4()
    allow_notification_permissions(monkeypatch)
    payload = event_payload(event_type, student_id)

    response = api_client.post(
        "/api/notifications/events/ingest/",
        payload,
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processed"
    assert Notification.objects.filter(recipient_profile_id=student_id, event_type=event_type).count() == 1
    assert DeliveryAttempt.objects.filter(channel=NotificationChannel.IN_APP, status=DeliveryStatus.SENT).count() == 1
    assert NotificationTemplate.objects.filter(event_type=event_type, channel=NotificationChannel.IN_APP).exists()


@pytest.mark.django_db
def test_event_ingestion_is_idempotent(api_client, access_token, monkeypatch):
    student_id = uuid4()
    allow_notification_permissions(monkeypatch)
    payload = event_payload("GradePublished", student_id)

    first_response = api_client.post(
        "/api/notifications/events/ingest/",
        payload,
        **auth_headers(access_token),
        format="json",
    )
    second_response = api_client.post(
        "/api/notifications/events/ingest/",
        payload,
        **auth_headers(access_token),
        format="json",
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["status"] == "duplicate"
    assert Notification.objects.count() == 1
    assert DeliveryAttempt.objects.count() == 1


@pytest.mark.django_db
def test_disabled_in_app_preference_skips_notification(api_client, access_token, monkeypatch):
    student_id = uuid4()
    allow_notification_permissions(monkeypatch)
    UserNotificationPreference.objects.create(
        profile_id=student_id,
        event_type="GradePublished",
        channel=NotificationChannel.IN_APP,
        enabled=False,
    )

    response = api_client.post(
        "/api/notifications/events/ingest/",
        event_payload("GradePublished", student_id),
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["status"] == "skipped"
    assert Notification.objects.count() == 0


@pytest.mark.django_db
def test_read_unread_and_read_all(api_client, access_token, monkeypatch):
    student_id = uuid4()
    other_student_id = uuid4()
    allow_notification_permissions(monkeypatch, allowed=set())
    patch_profile(monkeypatch, student_id)
    own_notification = Notification.objects.create(
        recipient_profile_id=student_id,
        event_type="GradePublished",
        title="Grade ready",
        body="Grade is ready.",
    )
    other_notification = Notification.objects.create(
        recipient_profile_id=other_student_id,
        event_type="GradePublished",
        title="Grade ready",
        body="Grade is ready.",
    )

    list_response = api_client.get("/api/notifications/", **auth_headers(access_token))
    read_response = api_client.post(
        f"/api/notifications/{own_notification.id}/read/",
        {},
        **auth_headers(access_token),
        format="json",
    )
    unread_response = api_client.post(
        f"/api/notifications/{own_notification.id}/unread/",
        {},
        **auth_headers(access_token),
        format="json",
    )
    denied_response = api_client.get(
        f"/api/notifications/{other_notification.id}/",
        **auth_headers(access_token),
    )
    read_all_response = api_client.post(
        "/api/notifications/read-all/",
        {},
        **auth_headers(access_token),
        format="json",
    )

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["results"]] == [str(own_notification.id)]
    assert read_response.status_code == 200
    assert read_response.json()["read_at"] is not None
    assert unread_response.status_code == 200
    assert unread_response.json()["read_at"] is None
    assert denied_response.status_code == 403
    assert read_all_response.status_code == 200
    assert read_all_response.json()["updated_count"] == 1


@pytest.mark.django_db
def test_delivery_failure_is_recorded(api_client, access_token, monkeypatch):
    student_id = uuid4()
    allow_notification_permissions(monkeypatch)

    response = api_client.post(
        "/api/notifications/events/ingest/",
        event_payload(
            "AssignmentDueSoon",
            student_id,
            force_delivery_failure=True,
            delivery_error_message="provider unavailable",
        ),
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 200
    attempt = DeliveryAttempt.objects.get()
    assert attempt.status == DeliveryStatus.FAILED
    assert attempt.error_message == "provider unavailable"


@pytest.mark.django_db
def test_preferences_owner_and_admin_paths(api_client, access_token, monkeypatch):
    student_id = uuid4()
    other_student_id = uuid4()
    allow_notification_permissions(monkeypatch, allowed=set())
    patch_profile(monkeypatch, student_id)

    own_response = api_client.post(
        "/api/notifications/preferences/",
        {"event_type": "GradePublished", "channel": "in_app", "enabled": False},
        **auth_headers(access_token),
        format="json",
    )
    denied_response = api_client.post(
        "/api/notifications/preferences/",
        {
            "profile_id": str(other_student_id),
            "event_type": "GradePublished",
            "channel": "in_app",
            "enabled": False,
        },
        **auth_headers(access_token),
        format="json",
    )
    allow_notification_permissions(monkeypatch)
    admin_response = api_client.post(
        "/api/notifications/preferences/",
        {
            "profile_id": str(other_student_id),
            "event_type": "GradePublished",
            "channel": "email",
            "enabled": False,
        },
        **auth_headers(access_token),
        format="json",
    )

    assert own_response.status_code == 200
    assert own_response.json()["profile_id"] == str(student_id)
    assert denied_response.status_code == 403
    assert admin_response.status_code == 200


@pytest.mark.django_db
def test_unauthorized_event_ingest_is_denied(api_client, access_token, monkeypatch):
    allow_notification_permissions(monkeypatch, allowed=set())

    response = api_client.post(
        "/api/notifications/events/ingest/",
        event_payload("StudentEnrolled", uuid4()),
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 403
