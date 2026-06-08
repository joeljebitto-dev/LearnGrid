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
    Question,
    QuestionBank,
    Quiz,
    QuizAnswer,
    QuizAttempt,
    QuizAttemptStatus,
    QuizQuestion,
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


def allow_assessment_view(monkeypatch, institution_id):
    def fake_remote_authorization_check(**kwargs):
        if kwargs["permission"] != "assessment.view":
            return False
        if kwargs["scope_type"] == "course":
            return True
        return kwargs["scope_type"] == "institution" and kwargs["scope_id"] == str(institution_id)

    monkeypatch.setattr(permissions, "remote_authorization_check", fake_remote_authorization_check)


def patch_student_context(monkeypatch, institution_id, student_profile_id, *, enrollment=True):
    monkeypatch.setattr(
        views,
        "get_course_context",
        lambda **kwargs: {"id": str(kwargs["course_id"]), "institution_id": str(institution_id)},
    )
    monkeypatch.setattr(
        views,
        "current_profile",
        lambda **_kwargs: {
            "id": str(student_profile_id),
            "profile_type": "student",
            "institution_id": str(institution_id),
        },
    )
    monkeypatch.setattr(services, "has_enrollment_access", lambda **_kwargs: enrollment)


def create_published_quiz(*, institution_id, course_id, question_count=1, **quiz_config):
    bank = QuestionBank.objects.create(
        institution_id=institution_id,
        owner_profile_id=uuid4(),
        title="Attempt Bank",
    )
    assessment = Assessment.objects.create(
        course_id=course_id,
        created_by_profile_id=uuid4(),
        assessment_type=AssessmentType.QUIZ,
        title="Published Quiz",
        status=AssessmentStatus.PUBLISHED,
        available_from=timezone.now() - timedelta(minutes=5),
        available_until=timezone.now() + timedelta(minutes=30),
    )
    quiz = Quiz.objects.create(assessment=assessment, **quiz_config)
    questions = []
    for index in range(question_count):
        question = Question.objects.create(
            question_bank=bank,
            question_type="multiple_choice",
            prompt=f"Question {index + 1}",
            choices=[{"id": "a", "text": "Wrong"}, {"id": "b", "text": "Right"}],
            correct_answer={"choice_id": "b"},
            points="2.00",
        )
        QuizQuestion.objects.create(quiz=quiz, question=question, position=index + 1)
        questions.append(question)
    return assessment, quiz, questions


@pytest.mark.django_db
def test_student_can_start_answer_and_submit_quiz_attempt(
    api_client,
    access_token,
    monkeypatch,
):
    institution_id = uuid4()
    course_id = uuid4()
    student_profile_id = uuid4()
    allow_assessment_view(monkeypatch, institution_id)
    patch_student_context(monkeypatch, institution_id, student_profile_id)
    events = []
    monkeypatch.setattr(
        services,
        "publish_assessment_event",
        lambda **kwargs: events.append(kwargs) or {"event_id": str(uuid4())},
    )
    assessment, _quiz, questions = create_published_quiz(
        institution_id=institution_id,
        course_id=course_id,
        max_attempts=1,
        time_limit_seconds=600,
    )

    start_response = api_client.post(
        f"/api/assessments/{assessment.id}/attempts/start/",
        **auth_headers(access_token),
    )
    assert start_response.status_code == 201
    start_body = start_response.json()
    assert start_body["attempt"]["attempt_number"] == 1
    assert "correct_answer" not in start_body["questions"][0]
    attempt_id = start_body["attempt"]["id"]

    answer_response = api_client.put(
        f"/api/assessments/attempts/{attempt_id}/answers/",
        {
            "answers": [
                {"question_id": str(questions[0].id), "answer_payload": {"choice_id": "b"}}
            ]
        },
        **auth_headers(access_token),
        format="json",
    )
    assert answer_response.status_code == 200
    assert QuizAnswer.objects.get().score == 2

    submit_response = api_client.post(
        f"/api/assessments/attempts/{attempt_id}/submit/",
        **auth_headers(access_token),
    )
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == QuizAttemptStatus.SUBMITTED
    assert submit_response.json()["score"] == "2.00"
    assert [event["event_type"] for event in events] == ["QuizAttemptStarted", "QuizSubmitted"]


@pytest.mark.django_db
def test_max_attempts_and_enrollment_are_enforced(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    course_id = uuid4()
    student_profile_id = uuid4()
    allow_assessment_view(monkeypatch, institution_id)
    patch_student_context(monkeypatch, institution_id, student_profile_id)
    assessment, _quiz, _questions = create_published_quiz(
        institution_id=institution_id,
        course_id=course_id,
        max_attempts=1,
    )

    first_response = api_client.post(
        f"/api/assessments/{assessment.id}/attempts/start/",
        **auth_headers(access_token),
    )
    assert first_response.status_code == 201

    second_response = api_client.post(
        f"/api/assessments/{assessment.id}/attempts/start/",
        **auth_headers(access_token),
    )
    assert second_response.status_code == 400

    other_assessment, _quiz, _questions = create_published_quiz(
        institution_id=institution_id,
        course_id=course_id,
    )
    patch_student_context(monkeypatch, institution_id, student_profile_id, enrollment=False)
    denied_response = api_client.post(
        f"/api/assessments/{other_assessment.id}/attempts/start/",
        **auth_headers(access_token),
    )
    assert denied_response.status_code == 403


@pytest.mark.django_db
def test_availability_window_and_auto_submit_are_enforced(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    course_id = uuid4()
    student_profile_id = uuid4()
    allow_assessment_view(monkeypatch, institution_id)
    patch_student_context(monkeypatch, institution_id, student_profile_id)
    closed_assessment, _quiz, _questions = create_published_quiz(
        institution_id=institution_id,
        course_id=course_id,
    )
    closed_assessment.available_until = timezone.now() - timedelta(minutes=1)
    closed_assessment.save()

    closed_response = api_client.post(
        f"/api/assessments/{closed_assessment.id}/attempts/start/",
        **auth_headers(access_token),
    )
    assert closed_response.status_code == 403

    assessment, quiz, questions = create_published_quiz(
        institution_id=institution_id,
        course_id=course_id,
        time_limit_seconds=1,
        auto_submit=True,
    )
    attempt = QuizAttempt.objects.create(quiz=quiz, student_profile_id=student_profile_id, attempt_number=1)
    QuizAttempt.objects.filter(id=attempt.id).update(started_at=timezone.now() - timedelta(seconds=5))

    answer_response = api_client.put(
        f"/api/assessments/attempts/{attempt.id}/answers/",
        {
            "answers": [
                {"question_id": str(questions[0].id), "answer_payload": {"choice_id": "b"}}
            ]
        },
        **auth_headers(access_token),
        format="json",
    )
    assert answer_response.status_code == 200
    assert answer_response.json()["attempt"]["status"] == QuizAttemptStatus.AUTO_SUBMITTED
    attempt.refresh_from_db()
    assert attempt.status == QuizAttemptStatus.AUTO_SUBMITTED
    assert SubmissionAuditLog.objects.filter(
        submission_id=attempt.id,
        event_type="attempt_auto_submitted",
    ).exists()
    assert assessment.status == AssessmentStatus.PUBLISHED


@pytest.mark.django_db
def test_randomized_question_order_is_persisted(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    course_id = uuid4()
    student_profile_id = uuid4()
    allow_assessment_view(monkeypatch, institution_id)
    patch_student_context(monkeypatch, institution_id, student_profile_id)
    assessment, _quiz, _questions = create_published_quiz(
        institution_id=institution_id,
        course_id=course_id,
        question_count=4,
        randomize_questions=True,
    )

    response = api_client.post(
        f"/api/assessments/{assessment.id}/attempts/start/",
        **auth_headers(access_token),
    )

    assert response.status_code == 201
    attempt_id = response.json()["attempt"]["id"]
    log = SubmissionAuditLog.objects.get(submission_id=attempt_id, event_type="attempt_started")
    response_order = [question["id"] for question in response.json()["questions"]]
    assert response_order == log.metadata["question_order"]


@pytest.mark.django_db
def test_auto_submit_endpoint_closes_attempt(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    course_id = uuid4()
    student_profile_id = uuid4()
    allow_assessment_view(monkeypatch, institution_id)
    patch_student_context(monkeypatch, institution_id, student_profile_id)
    _assessment, quiz, _questions = create_published_quiz(
        institution_id=institution_id,
        course_id=course_id,
    )
    attempt = QuizAttempt.objects.create(quiz=quiz, student_profile_id=student_profile_id, attempt_number=1)

    response = api_client.post(
        f"/api/assessments/attempts/{attempt.id}/auto-submit/",
        **auth_headers(access_token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == QuizAttemptStatus.AUTO_SUBMITTED
