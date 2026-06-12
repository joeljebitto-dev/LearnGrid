from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import jwt
import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.assessments import permissions, services, views
from apps.assessments.models import (
    Assessment,
    AssessmentStatus,
    AssessmentType,
    Assignment,
    AssignmentSubmission,
    AssignmentSubmissionStatus,
    SubmissionAuditLog,
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


def allow_permissions(monkeypatch, institution_id, permissions_allowed=None):
    permissions_allowed = permissions_allowed or {
        "submission.view",
        "submission.manage",
        "grade.manage",
    }

    def fake_remote_authorization_check(**kwargs):
        if kwargs["permission"] not in permissions_allowed:
            return False
        if kwargs["scope_type"] == "course":
            return True
        return kwargs["scope_type"] == "institution" and kwargs["scope_id"] == str(institution_id)

    monkeypatch.setattr(permissions, "remote_authorization_check", fake_remote_authorization_check)


def patch_context(
    monkeypatch, institution_id, profile_id, *, profile_type="student", enrolled=True
):
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
            "profile_type": profile_type,
            "institution_id": str(institution_id),
        },
    )
    monkeypatch.setattr(views, "has_enrollment_access", lambda **_kwargs: enrolled)
    monkeypatch.setattr(services, "has_enrollment_access", lambda **_kwargs: enrolled)
    monkeypatch.setattr(
        services, "validate_content_asset", lambda **kwargs: {"id": str(kwargs["asset_id"])}
    )


def create_assignment(*, course_id, due_at=None, allow_late=False):
    assessment = Assessment.objects.create(
        course_id=course_id,
        created_by_profile_id=uuid4(),
        assessment_type=AssessmentType.ASSIGNMENT,
        title="Essay",
        status=AssessmentStatus.PUBLISHED,
        available_from=timezone.now() - timedelta(minutes=5),
        available_until=timezone.now() + timedelta(days=1),
    )
    return Assignment.objects.create(
        assessment=assessment,
        due_at=due_at,
        allow_late_submission=allow_late,
        max_points="25.00",
    )


@pytest.mark.django_db
def test_student_can_save_and_submit_text_assignment(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    course_id = uuid4()
    student_id = uuid4()
    assignment = create_assignment(course_id=course_id)
    allow_permissions(monkeypatch, institution_id)
    patch_context(monkeypatch, institution_id, student_id)
    events = []
    monkeypatch.setattr(
        services,
        "publish_assessment_event",
        lambda **kwargs: events.append(kwargs) or {"event_id": str(uuid4())},
    )

    draft_response = api_client.post(
        f"/api/assessments/assignments/{assignment.id}/submissions/",
        {"submission_text": "My essay draft"},
        **auth_headers(access_token),
        format="json",
    )
    assert draft_response.status_code == 201
    submission_id = draft_response.json()["id"]
    assert draft_response.json()["status"] == AssignmentSubmissionStatus.DRAFT

    update_response = api_client.patch(
        f"/api/assessments/submissions/{submission_id}/",
        {"submission_text": "Final essay"},
        **auth_headers(access_token),
        format="json",
    )
    assert update_response.status_code == 200

    submit_response = api_client.post(
        f"/api/assessments/submissions/{submission_id}/submit/",
        **auth_headers(access_token),
    )
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == AssignmentSubmissionStatus.SUBMITTED
    assert SubmissionAuditLog.objects.filter(
        submission_id=submission_id,
        event_type="assignment_submitted",
    ).exists()
    assert events[-1]["event_type"] == "AssignmentSubmitted"


@pytest.mark.django_db
def test_attachment_validation_and_late_policy(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    course_id = uuid4()
    student_id = uuid4()
    allow_permissions(monkeypatch, institution_id)
    patch_context(monkeypatch, institution_id, student_id)
    rejected_assignment = create_assignment(
        course_id=course_id,
        due_at=timezone.now() - timedelta(minutes=1),
        allow_late=False,
    )

    rejected_response = api_client.post(
        f"/api/assessments/assignments/{rejected_assignment.id}/submissions/",
        {"submission_text": "Late work", "submit": True},
        **auth_headers(access_token),
        format="json",
    )
    assert rejected_response.status_code == 400

    accepted_assignment = create_assignment(
        course_id=course_id,
        due_at=timezone.now() - timedelta(minutes=1),
        allow_late=True,
    )
    asset_id = uuid4()
    accepted_response = api_client.post(
        f"/api/assessments/assignments/{accepted_assignment.id}/submissions/",
        {"attachment_asset_id": str(asset_id), "submit": True},
        **auth_headers(access_token),
        format="json",
    )
    assert accepted_response.status_code == 201
    assert accepted_response.json()["attachment_asset_id"] == str(asset_id)
    assert accepted_response.json()["status"] == AssignmentSubmissionStatus.LATE


@pytest.mark.django_db
def test_submission_owner_and_manager_access(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    course_id = uuid4()
    owner_id = uuid4()
    other_student_id = uuid4()
    assignment = create_assignment(course_id=course_id)
    submission = AssignmentSubmission.objects.create(
        assignment=assignment,
        student_profile_id=owner_id,
        submission_text="Private",
        status=AssignmentSubmissionStatus.SUBMITTED,
        submitted_at=timezone.now(),
    )
    allow_permissions(monkeypatch, institution_id)
    patch_context(monkeypatch, institution_id, other_student_id)

    denied_response = api_client.get(
        f"/api/assessments/submissions/{submission.id}/",
        **auth_headers(access_token),
    )
    assert denied_response.status_code == 403

    patch_context(monkeypatch, institution_id, uuid4(), profile_type="instructor")
    manager_response = api_client.get(
        f"/api/assessments/submissions/{submission.id}/",
        **auth_headers(access_token),
    )
    assert manager_response.status_code == 200


@pytest.mark.django_db
def test_grading_source_and_mark_graded(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    course_id = uuid4()
    instructor_id = uuid4()
    assignment = create_assignment(course_id=course_id)
    submission = AssignmentSubmission.objects.create(
        assignment=assignment,
        student_profile_id=uuid4(),
        submission_text="Ready to grade",
        status=AssignmentSubmissionStatus.SUBMITTED,
        submitted_at=timezone.now(),
    )
    allow_permissions(monkeypatch, institution_id)
    patch_context(monkeypatch, institution_id, instructor_id, profile_type="instructor")

    source_response = api_client.get(
        f"/api/assessments/grading/assignment-submissions/{submission.id}/",
        **auth_headers(access_token),
    )
    assert source_response.status_code == 200
    assert source_response.json()["submission_type"] == "assignment_submission"
    assert source_response.json()["max_score"] == "25.00"

    grade_record_id = uuid4()
    mark_response = api_client.post(
        f"/api/assessments/submissions/{submission.id}/mark-graded/",
        {"grade_record_id": str(grade_record_id)},
        **auth_headers(access_token),
        format="json",
    )
    assert mark_response.status_code == 200
    assert mark_response.json()["status"] == AssignmentSubmissionStatus.GRADED
    assert SubmissionAuditLog.objects.filter(
        submission_id=submission.id,
        event_type="assignment_submission_graded",
        metadata__grade_record_id=str(grade_record_id),
    ).exists()
