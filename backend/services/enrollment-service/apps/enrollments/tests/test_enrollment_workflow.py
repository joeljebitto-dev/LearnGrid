from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import jwt
import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.enrollments import permissions, services
from apps.enrollments.models import AccessGrant, Enrollment, EnrollmentHistory, EnrollmentStatus


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


def allow_enrollment(monkeypatch, institution_id):
    monkeypatch.setattr(
        permissions,
        "remote_authorization_check",
        lambda **kwargs: (
            kwargs["permission"] in {"enrollment.manage", "enrollment.view"}
            and kwargs["scope_type"] == "institution"
            and kwargs["scope_id"] == str(institution_id)
        )
        or (
            kwargs["permission"] == "enrollment.view"
            and kwargs["scope_type"] == "platform"
            and kwargs["scope_id"] is None
        ),
    )


@pytest.mark.django_db
def test_individual_enrollment_access_history_and_events(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    student_id = uuid4()
    course_id = uuid4()
    allow_enrollment(monkeypatch, institution_id)
    events = []
    monkeypatch.setattr(
        services,
        "publish_enrollment_event",
        lambda **kwargs: events.append(kwargs) or {"event_id": "evt"},
    )

    response = api_client.post(
        "/api/enrollments/",
        {
            "student_profile_id": str(student_id),
            "course_id": str(course_id),
            "institution_id": str(institution_id),
            "enrolled_by_profile_id": str(uuid4()),
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201
    enrollment_id = response.json()["id"]
    assert AccessGrant.objects.filter(student_profile_id=student_id, course_id=course_id).exists()
    assert EnrollmentHistory.objects.filter(enrollment_id=enrollment_id).count() == 1
    assert events[-1]["event_type"] == "StudentEnrolled"

    response = api_client.post(
        "/api/enrollments/",
        {
            "student_profile_id": str(student_id),
            "course_id": str(course_id),
            "institution_id": str(institution_id),
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 400

    response = api_client.get(
        "/api/enrollments/access/check/",
        {"student_profile_id": str(student_id), "course_id": str(course_id)},
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert response.json()["allowed"] is True

    response = api_client.post(
        f"/api/enrollments/{enrollment_id}/transition/",
        {"status": EnrollmentStatus.CANCELLED, "reason": "Dropped"},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["status"] == EnrollmentStatus.CANCELLED
    assert events[-1]["event_type"] == "StudentRemovedFromCourse"

    response = api_client.get(
        "/api/enrollments/access/check/",
        {"student_profile_id": str(student_id), "course_id": str(course_id)},
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert response.json()["allowed"] is False


@pytest.mark.django_db
def test_batch_and_cohort_jobs_create_summaries(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    course_id = uuid4()
    student_id = uuid4()
    allow_enrollment(monkeypatch, institution_id)

    response = api_client.post(
        "/api/enrollments/batch-enrollments/",
        {
            "batch_id": str(uuid4()),
            "course_id": str(course_id),
            "institution_id": str(institution_id),
            "requested_by_profile_id": str(uuid4()),
            "student_profile_ids": [str(student_id), str(student_id)],
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["summary"]["created"] == 1
    assert response.json()["summary"]["failed"] == 1
    assert Enrollment.objects.filter(student_profile_id=student_id, course_id=course_id).count() == 1

    response = api_client.post(
        "/api/enrollments/cohort-enrollments/",
        {
            "cohort_id": str(uuid4()),
            "course_id": str(uuid4()),
            "institution_id": str(institution_id),
            "requested_by_profile_id": str(uuid4()),
            "student_profile_ids": [str(uuid4())],
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["summary"]["created"] == 1
