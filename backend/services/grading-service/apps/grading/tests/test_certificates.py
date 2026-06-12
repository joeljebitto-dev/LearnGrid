from __future__ import annotations

import re
from datetime import timedelta
from uuid import uuid4

import jwt
import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.grading import permissions, services, views
from apps.grading.models import (
    Certificate,
    CertificateEligibility,
    GradeRecord,
    GradeRecordStatus,
    GradingRule,
    PublishedResult,
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


def allow_grade_permissions(monkeypatch, institution_id, allowed=None):
    if allowed is None:
        allowed = {"grade.view", "grade.manage"}

    def fake_remote_authorization_check(**kwargs):
        if kwargs["permission"] not in allowed:
            return False
        if kwargs["scope_type"] == "course":
            return True
        return kwargs["scope_type"] == "institution" and kwargs["scope_id"] == str(institution_id)

    monkeypatch.setattr(permissions, "remote_authorization_check", fake_remote_authorization_check)


def patch_context(monkeypatch, institution_id, profile_id):
    monkeypatch.setattr(
        views,
        "get_course_context",
        lambda **kwargs: {"id": str(kwargs["course_id"]), "institution_id": str(institution_id)},
    )
    monkeypatch.setattr(
        views,
        "current_profile",
        lambda **_kwargs: {
            "id": str(profile_id),
            "profile_type": "instructor",
            "institution_id": str(institution_id),
        },
    )


def create_published_result(*, student_id, course_id, score="85.00", max_score="100.00"):
    grade_record = GradeRecord.objects.create(
        student_profile_id=student_id,
        course_id=course_id,
        assessment_id=uuid4(),
        submission_id=uuid4(),
        score=score,
        max_score=max_score,
        status=GradeRecordStatus.PUBLISHED,
        published_at=timezone.now(),
    )
    return PublishedResult.objects.create(
        grade_record=grade_record,
        student_profile_id=student_id,
        course_id=course_id,
        published_score=score,
        published_by_profile_id=uuid4(),
    )


def evaluate_payload(student_id, course_id, certificate_asset_id=None):
    payload = {"student_profile_id": str(student_id), "course_id": str(course_id)}
    if certificate_asset_id:
        payload["certificate_asset_id"] = str(certificate_asset_id)
    return payload


@pytest.mark.django_db
def test_eligible_student_is_auto_issued_certificate_idempotently(
    api_client, access_token, monkeypatch
):
    institution_id = uuid4()
    manager_id = uuid4()
    student_id = uuid4()
    course_id = uuid4()
    allow_grade_permissions(monkeypatch, institution_id)
    patch_context(monkeypatch, institution_id, manager_id)
    create_published_result(student_id=student_id, course_id=course_id)
    monkeypatch.setattr(
        services,
        "fetch_course_progress",
        lambda **_kwargs: {"status": "completed", "completion_percent": "100.00"},
    )
    events = []
    monkeypatch.setattr(
        services,
        "publish_certificate_event",
        lambda **kwargs: events.append(kwargs) or {"event_id": str(uuid4())},
    )

    response = api_client.post(
        "/api/grading/certificates/eligibility/evaluate/",
        evaluate_payload(student_id, course_id),
        **auth_headers(access_token),
        format="json",
    )
    repeat_response = api_client.post(
        "/api/grading/certificates/eligibility/evaluate/",
        evaluate_payload(student_id, course_id),
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["eligibility"]["eligible"] is True
    assert body["eligibility"]["reason"] == "eligible"
    assert body["certificate"]["valid"] is True
    assert re.match(r"^LG-\d{8}-[A-Z0-9]{10}$", body["certificate"]["certificate_number"])
    assert events[-1]["event_type"] == "CertificateEligible"
    assert CertificateEligibility.objects.count() == 1
    assert Certificate.objects.count() == 1
    assert repeat_response.status_code == 200
    assert repeat_response.json()["certificate"]["id"] == body["certificate"]["id"]


@pytest.mark.django_db
def test_ineligible_reasons_are_stable(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    manager_id = uuid4()
    student_id = uuid4()
    course_id = uuid4()
    allow_grade_permissions(monkeypatch, institution_id)
    patch_context(monkeypatch, institution_id, manager_id)

    monkeypatch.setattr(services, "fetch_course_progress", lambda **_kwargs: None)
    missing_progress = api_client.post(
        "/api/grading/certificates/eligibility/evaluate/",
        evaluate_payload(student_id, course_id),
        **auth_headers(access_token),
        format="json",
    )
    assert missing_progress.json()["eligibility"]["reason"] == "course_progress_missing"

    monkeypatch.setattr(
        services,
        "fetch_course_progress",
        lambda **_kwargs: {"status": "in_progress", "completion_percent": "99.00"},
    )
    incomplete = api_client.post(
        "/api/grading/certificates/eligibility/evaluate/",
        evaluate_payload(student_id, course_id),
        **auth_headers(access_token),
        format="json",
    )
    assert incomplete.json()["eligibility"]["reason"] == "course_incomplete"

    monkeypatch.setattr(
        services,
        "fetch_course_progress",
        lambda **_kwargs: {"status": "completed", "completion_percent": "100.00"},
    )
    missing_results = api_client.post(
        "/api/grading/certificates/eligibility/evaluate/",
        evaluate_payload(student_id, course_id),
        **auth_headers(access_token),
        format="json",
    )
    assert missing_results.json()["eligibility"]["reason"] == "published_results_missing"

    create_published_result(
        student_id=student_id, course_id=course_id, score="60.00", max_score="100.00"
    )
    below_threshold = api_client.post(
        "/api/grading/certificates/eligibility/evaluate/",
        evaluate_payload(student_id, course_id),
        **auth_headers(access_token),
        format="json",
    )
    assert below_threshold.json()["eligibility"]["reason"] == "grade_below_threshold"
    assert below_threshold.json()["certificate"] is None


@pytest.mark.django_db
def test_course_level_certificate_threshold_overrides_default(
    api_client, access_token, monkeypatch
):
    institution_id = uuid4()
    manager_id = uuid4()
    student_id = uuid4()
    course_id = uuid4()
    allow_grade_permissions(monkeypatch, institution_id)
    patch_context(monkeypatch, institution_id, manager_id)
    GradingRule.objects.create(
        course_id=course_id,
        rule_type="percentage",
        configuration={"certificate_min_percent": "90"},
        created_by_profile_id=manager_id,
    )
    create_published_result(
        student_id=student_id, course_id=course_id, score="85.00", max_score="100.00"
    )
    monkeypatch.setattr(
        services,
        "fetch_course_progress",
        lambda **_kwargs: {"status": "completed", "completion_percent": "100.00"},
    )

    response = api_client.post(
        "/api/grading/certificates/eligibility/evaluate/",
        evaluate_payload(student_id, course_id),
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["threshold_percent"] == "90"
    assert response.json()["eligibility"]["reason"] == "grade_below_threshold"


@pytest.mark.django_db
def test_certificate_asset_linking_revoke_and_student_visibility(
    api_client, access_token, monkeypatch
):
    institution_id = uuid4()
    manager_id = uuid4()
    student_id = uuid4()
    course_id = uuid4()
    first_asset_id = uuid4()
    second_asset_id = uuid4()
    allow_grade_permissions(monkeypatch, institution_id)
    patch_context(monkeypatch, institution_id, manager_id)
    create_published_result(student_id=student_id, course_id=course_id)
    monkeypatch.setattr(
        services,
        "fetch_course_progress",
        lambda **_kwargs: {"status": "completed", "completion_percent": "100.00"},
    )
    validated_assets = []
    monkeypatch.setattr(
        services,
        "validate_content_asset",
        lambda **kwargs: validated_assets.append(str(kwargs["asset_id"]))
        or {"id": str(kwargs["asset_id"])},
    )

    issue_response = api_client.post(
        "/api/grading/certificates/eligibility/evaluate/",
        evaluate_payload(student_id, course_id, first_asset_id),
        **auth_headers(access_token),
        format="json",
    )
    certificate_id = issue_response.json()["certificate"]["id"]
    assert issue_response.json()["certificate"]["certificate_asset_id"] == str(first_asset_id)

    patch_response = api_client.patch(
        f"/api/grading/certificates/{certificate_id}/",
        {"certificate_asset_id": str(second_asset_id)},
        **auth_headers(access_token),
        format="json",
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["certificate_asset_id"] == str(second_asset_id)
    assert str(first_asset_id) in validated_assets
    assert str(second_asset_id) in validated_assets

    revoke_response = api_client.post(
        f"/api/grading/certificates/{certificate_id}/revoke/",
        {},
        **auth_headers(access_token),
        format="json",
    )
    assert revoke_response.status_code == 200
    assert revoke_response.json()["valid"] is False
    assert revoke_response.json()["revoked_at"] is not None

    allow_grade_permissions(monkeypatch, institution_id, allowed=set())
    monkeypatch.setattr(
        views,
        "current_profile",
        lambda **_kwargs: {"id": str(student_id), "profile_type": "student"},
    )
    list_response = api_client.get("/api/grading/certificates/", **auth_headers(access_token))
    detail_response = api_client.get(
        f"/api/grading/certificates/{certificate_id}/",
        **auth_headers(access_token),
    )
    assert list_response.status_code == 200
    assert list_response.json()["results"] == []
    assert detail_response.status_code == 403


@pytest.mark.django_db
def test_certificate_remote_failures_are_controlled(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    manager_id = uuid4()
    student_id = uuid4()
    course_id = uuid4()
    asset_id = uuid4()
    allow_grade_permissions(monkeypatch, institution_id)
    patch_context(monkeypatch, institution_id, manager_id)
    create_published_result(student_id=student_id, course_id=course_id)

    def broken_progress(**_kwargs):
        raise services.ProgressServiceError("Progress-service is unavailable.")

    monkeypatch.setattr(services, "fetch_course_progress", broken_progress)
    progress_response = api_client.post(
        "/api/grading/certificates/eligibility/evaluate/",
        evaluate_payload(student_id, course_id),
        **auth_headers(access_token),
        format="json",
    )
    assert progress_response.status_code == 502

    def broken_content(**_kwargs):
        raise services.ContentServiceError("Content-service is unavailable.")

    monkeypatch.setattr(services, "validate_content_asset", broken_content)
    content_response = api_client.post(
        "/api/grading/certificates/eligibility/evaluate/",
        evaluate_payload(student_id, course_id, asset_id),
        **auth_headers(access_token),
        format="json",
    )
    assert content_response.status_code == 502
