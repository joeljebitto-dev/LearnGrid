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
    Question,
    QuestionBank,
    Quiz,
    QuizQuestion,
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


def allow_assessment_permissions(monkeypatch, institution_id, *, manage=True, view_permission=True):
    def fake_remote_authorization_check(**kwargs):
        if kwargs["scope_type"] not in {"institution", "course"}:
            return False
        if kwargs["scope_type"] == "institution" and kwargs["scope_id"] != str(institution_id):
            return False
        if kwargs["permission"] == "assessment.manage":
            return manage
        if kwargs["permission"] == "assessment.view":
            return view_permission
        return False

    monkeypatch.setattr(permissions, "remote_authorization_check", fake_remote_authorization_check)


def patch_course_context(monkeypatch, institution_id):
    monkeypatch.setattr(
        views,
        "get_course_context",
        lambda **kwargs: {"id": str(kwargs["course_id"]), "institution_id": str(institution_id)},
    )


@pytest.mark.django_db
def test_authoring_workflow_creates_publishes_and_closes_quiz(
    api_client,
    access_token,
    monkeypatch,
):
    institution_id = uuid4()
    owner_profile_id = uuid4()
    course_id = uuid4()
    allow_assessment_permissions(monkeypatch, institution_id)
    patch_course_context(monkeypatch, institution_id)
    events = []
    monkeypatch.setattr(
        services,
        "publish_assessment_event",
        lambda **kwargs: events.append(kwargs) or {"event_id": str(uuid4())},
    )

    bank_response = api_client.post(
        "/api/assessments/question-banks/",
        {
            "institution_id": str(institution_id),
            "owner_profile_id": str(owner_profile_id),
            "title": "Midterm Bank",
        },
        **auth_headers(access_token),
        format="json",
    )
    assert bank_response.status_code == 201

    question_response = api_client.post(
        f"/api/assessments/question-banks/{bank_response.json()['id']}/questions/",
        {
            "question_type": "multiple_choice",
            "prompt": "What is 2 + 2?",
            "choices": [{"id": "a", "text": "3"}, {"id": "b", "text": "4"}],
            "correct_answer": {"choice_id": "b"},
            "points": "2.00",
        },
        **auth_headers(access_token),
        format="json",
    )
    assert question_response.status_code == 201
    question_id = question_response.json()["id"]

    assessment_response = api_client.post(
        "/api/assessments/",
        {
            "course_id": str(course_id),
            "created_by_profile_id": str(owner_profile_id),
            "assessment_type": "quiz",
            "title": "Week 1 Quiz",
            "quiz_config": {"max_attempts": 2, "time_limit_seconds": 600},
            "questions": [{"question_id": question_id, "position": 1}],
        },
        **auth_headers(access_token),
        format="json",
    )
    assert assessment_response.status_code == 201
    assessment_body = assessment_response.json()
    assert assessment_body["status"] == AssessmentStatus.DRAFT
    assert assessment_body["quiz"]["question_links"][0]["question"]["correct_answer"] == {
        "choice_id": "b"
    }

    publish_response = api_client.post(
        f"/api/assessments/{assessment_body['id']}/publish/",
        **auth_headers(access_token),
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == AssessmentStatus.PUBLISHED

    close_response = api_client.post(
        f"/api/assessments/{assessment_body['id']}/close/",
        **auth_headers(access_token),
    )
    assert close_response.status_code == 200
    assert close_response.json()["status"] == AssessmentStatus.CLOSED
    assert [event["event_type"] for event in events] == ["AssessmentPublished", "AssessmentClosed"]


@pytest.mark.django_db
def test_coding_questions_are_rejected_and_assignment_config_is_supported(
    api_client,
    access_token,
    monkeypatch,
):
    institution_id = uuid4()
    owner_profile_id = uuid4()
    course_id = uuid4()
    allow_assessment_permissions(monkeypatch, institution_id)
    patch_course_context(monkeypatch, institution_id)
    bank = QuestionBank.objects.create(
        institution_id=institution_id,
        owner_profile_id=owner_profile_id,
        title="Assignments",
    )

    coding_response = api_client.post(
        f"/api/assessments/question-banks/{bank.id}/questions/",
        {"question_type": "coding", "prompt": "Implement a function.", "points": "5.00"},
        **auth_headers(access_token),
        format="json",
    )
    assert coding_response.status_code == 400

    assignment_response = api_client.post(
        "/api/assessments/",
        {
            "course_id": str(course_id),
            "created_by_profile_id": str(owner_profile_id),
            "assessment_type": "assignment",
            "title": "Essay",
            "assignment_config": {"max_points": "25.00", "allow_late_submission": True},
        },
        **auth_headers(access_token),
        format="json",
    )
    assert assignment_response.status_code == 201
    assert assignment_response.json()["assignment"]["max_points"] == "25.00"
    assert Assignment.objects.count() == 1


@pytest.mark.django_db
def test_unauthorized_author_cannot_create_question_bank_or_assessment(
    api_client,
    access_token,
    monkeypatch,
):
    institution_id = uuid4()
    patch_course_context(monkeypatch, institution_id)
    monkeypatch.setattr(permissions, "remote_authorization_check", lambda **_kwargs: False)

    bank_response = api_client.post(
        "/api/assessments/question-banks/",
        {
            "institution_id": str(institution_id),
            "owner_profile_id": str(uuid4()),
            "title": "Denied",
        },
        **auth_headers(access_token),
        format="json",
    )
    assert bank_response.status_code == 403

    assessment_response = api_client.post(
        "/api/assessments/",
        {
            "course_id": str(uuid4()),
            "created_by_profile_id": str(uuid4()),
            "assessment_type": "quiz",
            "title": "Denied Quiz",
        },
        **auth_headers(access_token),
        format="json",
    )
    assert assessment_response.status_code == 403


@pytest.mark.django_db
def test_draft_assessments_are_hidden_from_student_discovery(
    api_client,
    access_token,
    monkeypatch,
):
    institution_id = uuid4()
    course_id = uuid4()
    student_profile_id = uuid4()
    patch_course_context(monkeypatch, institution_id)
    allow_assessment_permissions(monkeypatch, institution_id, manage=False, view_permission=True)
    monkeypatch.setattr(
        views,
        "current_profile",
        lambda **_kwargs: {"id": str(student_profile_id), "profile_type": "student"},
    )
    monkeypatch.setattr(views, "has_enrollment_access", lambda **_kwargs: True)
    Assessment.objects.create(
        course_id=course_id,
        created_by_profile_id=uuid4(),
        assessment_type=AssessmentType.QUIZ,
        title="Draft Quiz",
    )
    published = Assessment.objects.create(
        course_id=course_id,
        created_by_profile_id=uuid4(),
        assessment_type=AssessmentType.QUIZ,
        title="Published Quiz",
        status=AssessmentStatus.PUBLISHED,
    )
    Quiz.objects.create(assessment=published)

    response = api_client.get(
        "/api/assessments/",
        {"course_id": str(course_id)},
        **auth_headers(access_token),
    )

    assert response.status_code == 200
    titles = [item["title"] for item in response.json()["results"]]
    assert titles == ["Published Quiz"]


@pytest.mark.django_db
def test_question_replacement_rejects_duplicate_question_ids(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    course_id = uuid4()
    bank = QuestionBank.objects.create(
        institution_id=institution_id,
        owner_profile_id=uuid4(),
        title="Bank",
    )
    question = Question.objects.create(
        question_bank=bank,
        question_type="true_false",
        prompt="Django is Python.",
        correct_answer={"value": True},
        points="1.00",
    )
    assessment = Assessment.objects.create(
        course_id=course_id,
        created_by_profile_id=uuid4(),
        assessment_type=AssessmentType.QUIZ,
        title="Quiz",
    )
    Quiz.objects.create(assessment=assessment)
    allow_assessment_permissions(monkeypatch, institution_id)
    patch_course_context(monkeypatch, institution_id)

    response = api_client.put(
        f"/api/assessments/{assessment.id}/questions/",
        {
            "questions": [
                {"question_id": str(question.id), "position": 1},
                {"question_id": str(question.id), "position": 2},
            ]
        },
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 400
    assert QuizQuestion.objects.count() == 0
