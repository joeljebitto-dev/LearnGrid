from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import jwt
import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.grading import permissions, services, views
from apps.grading.models import (
    GradeHistory,
    GradeRecord,
    GradeRecordStatus,
    ManualReviewStatus,
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
        lambda **_kwargs: {"id": str(profile_id), "profile_type": "instructor", "institution_id": str(institution_id)},
    )


def grading_source(*, course_id, student_id, assessment_id=None, submission_id=None, score="8.00", max_score="10.00"):
    return {
        "submission_type": "quiz_attempt",
        "submission_id": str(submission_id or uuid4()),
        "student_profile_id": str(student_id),
        "course_id": str(course_id),
        "assessment_id": str(assessment_id or uuid4()),
        "score": score,
        "max_score": max_score,
        "status": "submitted",
        "source_payload": {"attempt_number": 1},
    }


@pytest.mark.django_db
def test_grading_rule_crud(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    profile_id = uuid4()
    course_id = uuid4()
    allow_grade_permissions(monkeypatch, institution_id)
    patch_context(monkeypatch, institution_id, profile_id)

    create_response = api_client.post(
        "/api/grading/rules/",
        {
            "course_id": str(course_id),
            "rule_type": "points",
            "configuration": {"drop_lowest": 0},
            "created_by_profile_id": str(profile_id),
        },
        **auth_headers(access_token),
        format="json",
    )
    assert create_response.status_code == 201
    rule_id = create_response.json()["id"]

    update_response = api_client.patch(
        f"/api/grading/rules/{rule_id}/",
        {"configuration": {"drop_lowest": 1}},
        **auth_headers(access_token),
        format="json",
    )
    assert update_response.status_code == 200
    assert update_response.json()["configuration"] == {"drop_lowest": 1}


@pytest.mark.django_db
def test_automated_quiz_calculation_writes_history_and_event(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    profile_id = uuid4()
    course_id = uuid4()
    student_id = uuid4()
    source = grading_source(course_id=course_id, student_id=student_id)
    allow_grade_permissions(monkeypatch, institution_id)
    patch_context(monkeypatch, institution_id, profile_id)
    monkeypatch.setattr(views, "fetch_grading_source", lambda **_kwargs: source)
    events = []
    monkeypatch.setattr(
        services,
        "publish_grade_event",
        lambda **kwargs: events.append(kwargs) or {"event_id": str(uuid4())},
    )

    response = api_client.post(
        "/api/grading/records/calculate/",
        {"submission_type": "quiz_attempt", "submission_id": source["submission_id"]},
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["score"] == "8.00"
    assert body["status"] == GradeRecordStatus.CALCULATED
    assert GradeHistory.objects.filter(grade_record_id=body["id"]).count() == 1
    assert events[-1]["event_type"] == "GradeCalculated"


@pytest.mark.django_db
def test_manual_review_override_and_publish(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    profile_id = uuid4()
    course_id = uuid4()
    student_id = uuid4()
    source = grading_source(
        course_id=course_id,
        student_id=student_id,
        submission_id=uuid4(),
        score=None,
        max_score="25.00",
    )
    source["submission_type"] = "assignment_submission"
    allow_grade_permissions(monkeypatch, institution_id)
    patch_context(monkeypatch, institution_id, profile_id)
    monkeypatch.setattr(views, "fetch_grading_source", lambda **_kwargs: source)
    marked = []
    events = []
    monkeypatch.setattr(
        services,
        "mark_assignment_submission_graded",
        lambda **kwargs: marked.append(kwargs) or {"status": "graded"},
    )
    monkeypatch.setattr(
        services,
        "publish_grade_event",
        lambda **kwargs: events.append(kwargs) or {"event_id": str(uuid4())},
    )

    review_response = api_client.post(
        "/api/grading/records/manual-reviews/",
        {"submission_type": "assignment_submission", "submission_id": source["submission_id"]},
        **auth_headers(access_token),
        format="json",
    )
    assert review_response.status_code == 201
    review_id = review_response.json()["id"]
    assert review_response.json()["status"] == ManualReviewStatus.PENDING

    complete_response = api_client.post(
        f"/api/grading/manual-reviews/{review_id}/complete/",
        {"score": "21.00", "feedback": "Good work"},
        **auth_headers(access_token),
        format="json",
    )
    assert complete_response.status_code == 200
    grade_id = complete_response.json()["id"]
    assert complete_response.json()["status"] == GradeRecordStatus.REVIEWED

    bad_override = api_client.post(
        f"/api/grading/records/{grade_id}/override/",
        {"score": "22.00", "change_reason": ""},
        **auth_headers(access_token),
        format="json",
    )
    assert bad_override.status_code == 400

    override_response = api_client.post(
        f"/api/grading/records/{grade_id}/override/",
        {"score": "23.00", "change_reason": "Rubric correction"},
        **auth_headers(access_token),
        format="json",
    )
    assert override_response.status_code == 200
    assert override_response.json()["status"] == GradeRecordStatus.OVERRIDDEN

    publish_response = api_client.post(
        f"/api/grading/records/{grade_id}/publish/",
        {"published_feedback": "Published feedback"},
        **auth_headers(access_token),
        format="json",
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["published_score"] == "23.00"
    assert PublishedResult.objects.filter(grade_record_id=grade_id).exists()
    assert str(marked[-1]["submission_id"]) == source["submission_id"]
    assert events[-1]["event_type"] == "GradePublished"
    assert GradeHistory.objects.filter(grade_record_id=grade_id).count() == 3


@pytest.mark.django_db
def test_published_result_owner_visibility(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    student_id = uuid4()
    other_student_id = uuid4()
    course_id = uuid4()
    grade_record = GradeRecord.objects.create(
        student_profile_id=student_id,
        course_id=course_id,
        assessment_id=uuid4(),
        submission_id=uuid4(),
        score="9.00",
        max_score="10.00",
        status=GradeRecordStatus.PUBLISHED,
        published_at=timezone.now(),
    )
    result = PublishedResult.objects.create(
        grade_record=grade_record,
        student_profile_id=student_id,
        course_id=course_id,
        published_score="9.00",
        published_by_profile_id=uuid4(),
    )
    allow_grade_permissions(monkeypatch, institution_id, allowed=set())
    monkeypatch.setattr(
        views,
        "current_profile",
        lambda **_kwargs: {"id": str(student_id), "profile_type": "student"},
    )

    own_response = api_client.get(
        f"/api/grading/results/{result.id}/",
        **auth_headers(access_token),
    )
    assert own_response.status_code == 200

    monkeypatch.setattr(
        views,
        "current_profile",
        lambda **_kwargs: {"id": str(other_student_id), "profile_type": "student"},
    )
    denied_response = api_client.get(
        f"/api/grading/results/{result.id}/",
        **auth_headers(access_token),
    )
    assert denied_response.status_code == 403


@pytest.mark.django_db
def test_assessment_service_failure_returns_controlled_error(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    profile_id = uuid4()
    allow_grade_permissions(monkeypatch, institution_id)
    patch_context(monkeypatch, institution_id, profile_id)

    def broken_source(**_kwargs):
        raise services.AssessmentServiceError("Assessment-service is unavailable.")

    monkeypatch.setattr(views, "fetch_grading_source", broken_source)
    response = api_client.post(
        "/api/grading/records/calculate/",
        {"submission_type": "quiz_attempt", "submission_id": str(uuid4())},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 502


@pytest.mark.django_db
def test_unauthorized_grade_flow_is_denied(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    profile_id = uuid4()
    course_id = uuid4()
    monkeypatch.setattr(permissions, "remote_authorization_check", lambda **_kwargs: False)
    patch_context(monkeypatch, institution_id, profile_id)

    response = api_client.post(
        "/api/grading/rules/",
        {
            "course_id": str(course_id),
            "rule_type": "points",
            "created_by_profile_id": str(profile_id),
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 403
