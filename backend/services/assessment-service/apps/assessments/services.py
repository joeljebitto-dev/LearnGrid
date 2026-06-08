from __future__ import annotations

import json
import logging
import random
import uuid
from datetime import timedelta
from decimal import Decimal
from typing import Any
from urllib import error, parse, request as urlrequest

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError

from .models import (
    Assessment,
    AssessmentStatus,
    AssessmentType,
    Assignment,
    AssignmentSubmission,
    AssignmentSubmissionStatus,
    Question,
    QuestionBank,
    QuestionStatus,
    QuestionType,
    Quiz,
    QuizAnswer,
    QuizAttempt,
    QuizAttemptStatus,
    QuizQuestion,
    SubmissionAuditLog,
    SubmissionType,
)


logger = logging.getLogger(__name__)


class CourseServiceError(APIException):
    status_code = 502
    default_code = "course_service_error"
    default_detail = "Course-service request failed."


class UserServiceError(APIException):
    status_code = 502
    default_code = "user_service_error"
    default_detail = "User-service request failed."


class EnrollmentServiceError(APIException):
    status_code = 502
    default_code = "enrollment_service_error"
    default_detail = "Enrollment-service request failed."


class ContentServiceError(APIException):
    status_code = 502
    default_code = "content_service_error"
    default_detail = "Content-service request failed."


def auth_token(request) -> str:
    return str(request.auth)


def _json_request(
    *,
    base_url: str,
    path: str,
    token: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
    error_class: type[APIException] = APIException,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}{path}"
    if query:
        url = f"{url}?{parse.urlencode({key: str(value) for key, value in query.items() if value is not None})}"
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urlrequest.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urlrequest.urlopen(request, timeout=3) as response:
            if response.status >= 400:
                raise error_class()
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except error.HTTPError as exc:
        if exc.code == 404:
            raise NotFound("Remote resource was not found.") from exc
        if exc.code in {401, 403}:
            raise PermissionDenied("Remote service denied access.") from exc
        raise error_class(f"Remote service returned HTTP {exc.code}.") from exc
    except (error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise error_class("Remote service is unavailable.") from exc


def get_course_context(*, token: str, course_id) -> dict[str, Any]:
    data = _json_request(
        base_url=settings.COURSE_SERVICE_BASE_URL,
        path=f"/api/courses/{course_id}/",
        token=token,
        error_class=CourseServiceError,
    )
    if not data.get("institution_id"):
        raise CourseServiceError("Course-service response did not include institution_id.")
    return data


def current_profile(*, token: str) -> dict[str, Any]:
    return _json_request(
        base_url=settings.USER_SERVICE_BASE_URL,
        path="/api/users/profiles/me/",
        token=token,
        error_class=UserServiceError,
    )


def require_student_profile(profile: dict[str, Any]) -> None:
    if profile.get("profile_type") != "student":
        raise PermissionDenied("Assessment attempts require a student profile.")


def has_enrollment_access(*, token: str, student_profile_id, course_id) -> bool:
    data = _json_request(
        base_url=settings.ENROLLMENT_SERVICE_BASE_URL,
        path="/api/enrollments/access/check/",
        token=token,
        query={"student_profile_id": student_profile_id, "course_id": course_id},
        error_class=EnrollmentServiceError,
    )
    return data.get("allowed") is True


def validate_content_asset(*, token: str, asset_id) -> dict[str, Any]:
    if not asset_id:
        return {}
    return _json_request(
        base_url=settings.CONTENT_SERVICE_BASE_URL,
        path=f"/api/content/assets/{asset_id}/",
        token=token,
        error_class=ContentServiceError,
    )


def create_question_bank(*, validated_data: dict[str, Any]) -> QuestionBank:
    return QuestionBank.objects.create(**validated_data)


def update_question_bank(*, question_bank: QuestionBank, validated_data: dict[str, Any]) -> QuestionBank:
    for field in ["title", "description"]:
        if field in validated_data:
            setattr(question_bank, field, validated_data[field])
    question_bank.save()
    return question_bank


def archive_question_bank(*, question_bank: QuestionBank) -> QuestionBank:
    question_bank.deleted_at = timezone.now()
    question_bank.save(update_fields=["deleted_at", "updated_at"])
    Question.objects.filter(question_bank=question_bank, deleted_at__isnull=True).update(
        status=QuestionStatus.ARCHIVED,
        deleted_at=question_bank.deleted_at,
    )
    return question_bank


def create_question(*, question_bank: QuestionBank, validated_data: dict[str, Any]) -> Question:
    return Question.objects.create(question_bank=question_bank, **validated_data)


def update_question(*, question: Question, validated_data: dict[str, Any]) -> Question:
    for field in ["question_type", "prompt", "choices", "correct_answer", "points", "status"]:
        if field in validated_data:
            setattr(question, field, validated_data[field])
    question.save()
    return question


def archive_question(*, question: Question) -> Question:
    question.status = QuestionStatus.ARCHIVED
    question.deleted_at = timezone.now()
    question.save(update_fields=["status", "deleted_at", "updated_at"])
    return question


@transaction.atomic
def create_assessment(*, validated_data: dict[str, Any]) -> Assessment:
    quiz_config = validated_data.pop("quiz_config", None)
    assignment_config = validated_data.pop("assignment_config", None)
    questions = validated_data.pop("questions", [])
    assessment = Assessment.objects.create(status=AssessmentStatus.DRAFT, **validated_data)

    if assessment.assessment_type in {AssessmentType.QUIZ, AssessmentType.EXAM}:
        Quiz.objects.create(assessment=assessment, **_default_quiz_config(quiz_config or {}))
        if questions:
            replace_quiz_questions(assessment=assessment, question_payloads=questions)
    elif assessment.assessment_type == AssessmentType.ASSIGNMENT:
        Assignment.objects.create(assessment=assessment, **_default_assignment_config(assignment_config or {}))
    return assessment


@transaction.atomic
def update_assessment(*, assessment: Assessment, validated_data: dict[str, Any]) -> Assessment:
    quiz_config = validated_data.pop("quiz_config", None)
    assignment_config = validated_data.pop("assignment_config", None)
    questions = validated_data.pop("questions", None)

    for field in ["course_id", "lesson_id", "title", "description", "available_from", "available_until"]:
        if field in validated_data:
            setattr(assessment, field, validated_data[field])
    assessment.save()

    if quiz_config is not None and hasattr(assessment, "quiz"):
        update_quiz_config(quiz=assessment.quiz, validated_data=quiz_config)
    if assignment_config is not None and hasattr(assessment, "assignment"):
        update_assignment_config(assignment=assessment.assignment, validated_data=assignment_config)
    if questions is not None:
        replace_quiz_questions(assessment=assessment, question_payloads=questions)
    return assessment


def update_quiz_config(*, quiz: Quiz, validated_data: dict[str, Any]) -> Quiz:
    for field in [
        "time_limit_seconds",
        "max_attempts",
        "randomize_questions",
        "auto_submit",
        "grading_policy",
    ]:
        if field in validated_data:
            setattr(quiz, field, validated_data[field])
    quiz.save()
    return quiz


def update_assignment_config(*, assignment: Assignment, validated_data: dict[str, Any]) -> Assignment:
    for field in ["due_at", "allow_late_submission", "max_points", "resource_asset_id"]:
        if field in validated_data:
            setattr(assignment, field, validated_data[field])
    assignment.save()
    return assignment


def save_assignment_submission(
    *,
    assignment: Assignment,
    token: str,
    profile: dict[str, Any],
    validated_data: dict[str, Any],
    submit: bool = False,
    correlation_id: str | None = None,
) -> AssignmentSubmission:
    require_student_profile(profile)
    _validate_assignment_available(assignment)
    if not has_enrollment_access(
        token=token,
        student_profile_id=profile["id"],
        course_id=assignment.assessment.course_id,
    ):
        raise PermissionDenied("Student does not have active access to this course.")
    if attachment_asset_id := validated_data.get("attachment_asset_id"):
        validate_content_asset(token=token, asset_id=attachment_asset_id)

    submission, created = AssignmentSubmission.objects.get_or_create(
        assignment=assignment,
        student_profile_id=profile["id"],
        defaults={"status": AssignmentSubmissionStatus.DRAFT},
    )
    if submission.status not in {AssignmentSubmissionStatus.DRAFT, AssignmentSubmissionStatus.SUBMITTED, AssignmentSubmissionStatus.LATE}:
        raise ValidationError({"submission": "Submission cannot be changed in its current status."})

    for field in ["submission_text", "attachment_asset_id"]:
        if field in validated_data:
            setattr(submission, field, validated_data[field])
    if submit:
        _finalize_assignment_submission(submission=submission, actor_profile_id=profile["id"], correlation_id=correlation_id)
    else:
        submission.status = AssignmentSubmissionStatus.DRAFT
        submission.save()
        SubmissionAuditLog.objects.create(
            submission_type=SubmissionType.ASSIGNMENT_SUBMISSION,
            submission_id=submission.id,
            event_type="assignment_submission_created" if created else "assignment_submission_saved",
            actor_profile_id=profile["id"],
            metadata={"assignment_id": str(assignment.id)},
        )
    return submission


def update_assignment_submission(
    *,
    submission: AssignmentSubmission,
    token: str,
    profile: dict[str, Any],
    validated_data: dict[str, Any],
) -> AssignmentSubmission:
    if str(submission.student_profile_id) != str(profile.get("id")):
        raise PermissionDenied("Submission belongs to another profile.")
    if submission.status != AssignmentSubmissionStatus.DRAFT:
        raise ValidationError({"submission": "Only draft submissions can be updated."})
    if attachment_asset_id := validated_data.get("attachment_asset_id"):
        validate_content_asset(token=token, asset_id=attachment_asset_id)
    for field in ["submission_text", "attachment_asset_id"]:
        if field in validated_data:
            setattr(submission, field, validated_data[field])
    submission.save()
    SubmissionAuditLog.objects.create(
        submission_type=SubmissionType.ASSIGNMENT_SUBMISSION,
        submission_id=submission.id,
        event_type="assignment_submission_saved",
        actor_profile_id=profile["id"],
        metadata={"assignment_id": str(submission.assignment_id)},
    )
    return submission


def submit_assignment_submission(
    *,
    submission: AssignmentSubmission,
    actor_profile_id,
    correlation_id: str | None = None,
) -> AssignmentSubmission:
    if submission.status not in {AssignmentSubmissionStatus.DRAFT, AssignmentSubmissionStatus.SUBMITTED, AssignmentSubmissionStatus.LATE}:
        raise ValidationError({"submission": "Submission cannot be submitted in its current status."})
    _validate_assignment_available(submission.assignment)
    return _finalize_assignment_submission(
        submission=submission,
        actor_profile_id=actor_profile_id,
        correlation_id=correlation_id,
    )


def mark_assignment_submission_graded(
    *,
    submission: AssignmentSubmission,
    actor_profile_id,
    grade_record_id=None,
) -> AssignmentSubmission:
    previous_status = submission.status
    submission.status = AssignmentSubmissionStatus.GRADED
    submission.save(update_fields=["status", "updated_at"])
    SubmissionAuditLog.objects.create(
        submission_type=SubmissionType.ASSIGNMENT_SUBMISSION,
        submission_id=submission.id,
        event_type="assignment_submission_graded",
        actor_profile_id=actor_profile_id,
        metadata={
            "previous_status": previous_status,
            "grade_record_id": str(grade_record_id) if grade_record_id else None,
        },
    )
    return submission


@transaction.atomic
def replace_quiz_questions(*, assessment: Assessment, question_payloads: list[dict[str, Any]]) -> list[QuizQuestion]:
    if assessment.assessment_type not in {AssessmentType.QUIZ, AssessmentType.EXAM}:
        raise ValidationError({"questions": "Only quizzes and exams support ordered questions."})
    quiz = assessment.quiz
    if not question_payloads:
        quiz.question_links.all().delete()
        return []

    question_ids = [item["question_id"] for item in question_payloads]
    if len(set(question_ids)) != len(question_ids):
        raise ValidationError({"questions": "Question IDs must be unique."})

    questions = {
        question.id: question
        for question in Question.objects.select_related("question_bank").filter(
            id__in=question_ids,
            deleted_at__isnull=True,
            question_bank__deleted_at__isnull=True,
        )
    }
    missing = set(question_ids) - set(questions)
    if missing:
        raise ValidationError({"questions": "All questions must exist and be active."})

    normalized = []
    used_positions: set[int] = set()
    for index, item in enumerate(question_payloads, start=1):
        position = item.get("position") or index
        if position in used_positions:
            raise ValidationError({"questions": "Question positions must be unique."})
        used_positions.add(position)
        normalized.append(
            {
                "question": questions[item["question_id"]],
                "position": position,
                "points_override": item.get("points_override"),
            }
        )

    quiz.question_links.all().delete()
    return [
        QuizQuestion.objects.create(
            quiz=quiz,
            question=item["question"],
            position=item["position"],
            points_override=item.get("points_override"),
        )
        for item in normalized
    ]


def publish_assessment(*, assessment: Assessment, correlation_id: str | None = None) -> Assessment:
    if assessment.assessment_type in {AssessmentType.QUIZ, AssessmentType.EXAM}:
        if not hasattr(assessment, "quiz") or not assessment.quiz.question_links.exists():
            raise ValidationError({"questions": "Published quizzes and exams require at least one question."})
    if assessment.assessment_type == AssessmentType.ASSIGNMENT and not hasattr(assessment, "assignment"):
        raise ValidationError({"assignment_config": "Published assignments require assignment configuration."})
    assessment.status = AssessmentStatus.PUBLISHED
    assessment.deleted_at = None
    assessment.save(update_fields=["status", "deleted_at", "updated_at"])
    publish_assessment_event(
        event_type="AssessmentPublished",
        aggregate_id=assessment.id,
        correlation_id=correlation_id,
        payload={"course_id": str(assessment.course_id), "assessment_type": assessment.assessment_type},
    )
    return assessment


def close_assessment(*, assessment: Assessment, correlation_id: str | None = None) -> Assessment:
    assessment.status = AssessmentStatus.CLOSED
    assessment.save(update_fields=["status", "updated_at"])
    publish_assessment_event(
        event_type="AssessmentClosed",
        aggregate_id=assessment.id,
        correlation_id=correlation_id,
        payload={"course_id": str(assessment.course_id), "assessment_type": assessment.assessment_type},
    )
    return assessment


def archive_assessment(*, assessment: Assessment) -> Assessment:
    assessment.status = AssessmentStatus.ARCHIVED
    assessment.deleted_at = timezone.now()
    assessment.save(update_fields=["status", "deleted_at", "updated_at"])
    return assessment


@transaction.atomic
def start_quiz_attempt(
    *,
    assessment: Assessment,
    token: str,
    profile: dict[str, Any],
    correlation_id: str | None = None,
) -> QuizAttempt:
    require_student_profile(profile)
    if assessment.assessment_type not in {AssessmentType.QUIZ, AssessmentType.EXAM}:
        raise ValidationError({"assessment": "Only quizzes and exams support attempts."})
    if assessment.status != AssessmentStatus.PUBLISHED or assessment.deleted_at is not None:
        raise PermissionDenied("Assessment is not available.")
    _validate_assessment_window(assessment)
    if not has_enrollment_access(
        token=token,
        student_profile_id=profile["id"],
        course_id=assessment.course_id,
    ):
        raise PermissionDenied("Student does not have active access to this course.")

    quiz = assessment.quiz
    if not quiz.question_links.exists():
        raise ValidationError({"questions": "Assessment has no questions."})
    prior_attempts = QuizAttempt.objects.filter(quiz=quiz, student_profile_id=profile["id"]).count()
    if quiz.max_attempts is not None and prior_attempts >= quiz.max_attempts:
        raise ValidationError({"max_attempts": "Maximum attempts reached."})

    attempt = QuizAttempt.objects.create(
        quiz=quiz,
        student_profile_id=profile["id"],
        attempt_number=prior_attempts + 1,
    )
    question_order = _question_order_for_attempt(attempt)
    SubmissionAuditLog.objects.create(
        submission_type=SubmissionType.QUIZ_ATTEMPT,
        submission_id=attempt.id,
        event_type="attempt_started",
        actor_profile_id=profile["id"],
        metadata={"question_order": [str(question_id) for question_id in question_order]},
    )
    publish_assessment_event(
        event_type="QuizAttemptStarted",
        aggregate_id=attempt.id,
        correlation_id=correlation_id,
        payload={
            "assessment_id": str(assessment.id),
            "quiz_id": str(quiz.id),
            "course_id": str(assessment.course_id),
            "student_profile_id": str(profile["id"]),
            "attempt_number": attempt.attempt_number,
        },
    )
    return attempt


def save_attempt_answers(*, attempt: QuizAttempt, answers: list[dict[str, Any]]) -> QuizAttempt:
    if attempt.status != QuizAttemptStatus.STARTED:
        raise ValidationError({"attempt": "Attempt is already closed."})
    deadline = attempt_deadline(attempt)
    if deadline and timezone.now() > deadline:
        if attempt.quiz.auto_submit:
            return submit_attempt(
                attempt=attempt,
                actor_profile_id=attempt.student_profile_id,
                auto=True,
            )
        raise ValidationError({"attempt": "Attempt time limit has expired."})

    allowed_questions = {
        link.question_id: link
        for link in QuizQuestion.objects.select_related("question").filter(quiz=attempt.quiz)
    }
    with transaction.atomic():
        for item in answers:
            question_id = item["question_id"]
            if question_id not in allowed_questions:
                raise ValidationError({"question_id": "Question does not belong to this attempt."})
            link = allowed_questions[question_id]
            score = score_answer(question=link.question, answer_payload=item["answer_payload"], link=link)
            defaults: dict[str, Any] = {"answer_payload": item["answer_payload"], "score": score}
            if score is not None:
                defaults["graded_at"] = timezone.now()
            QuizAnswer.objects.update_or_create(
                quiz_attempt=attempt,
                question_id=question_id,
                defaults=defaults,
            )
    return attempt


@transaction.atomic
def submit_attempt(
    *,
    attempt: QuizAttempt,
    actor_profile_id,
    auto: bool = False,
    correlation_id: str | None = None,
) -> QuizAttempt:
    if attempt.status != QuizAttemptStatus.STARTED:
        raise ValidationError({"attempt": "Attempt is already closed."})
    deadline = attempt_deadline(attempt)
    if deadline and timezone.now() > deadline:
        if attempt.quiz.auto_submit:
            auto = True
        elif not auto:
            raise ValidationError({"attempt": "Attempt time limit has expired."})

    total = Decimal("0")
    for answer in attempt.answers.select_related("question").all():
        link = QuizQuestion.objects.get(quiz=attempt.quiz, question=answer.question)
        answer.score = score_answer(question=answer.question, answer_payload=answer.answer_payload, link=link)
        if answer.score is not None:
            answer.graded_at = timezone.now()
            total += answer.score
        answer.save()

    attempt.status = QuizAttemptStatus.AUTO_SUBMITTED if auto else QuizAttemptStatus.SUBMITTED
    attempt.submitted_at = timezone.now()
    attempt.score = total
    attempt.save(update_fields=["status", "submitted_at", "score", "updated_at"])
    SubmissionAuditLog.objects.create(
        submission_type=SubmissionType.QUIZ_ATTEMPT,
        submission_id=attempt.id,
        event_type="attempt_auto_submitted" if auto else "attempt_submitted",
        actor_profile_id=actor_profile_id,
        metadata={"score": str(total), "auto": auto},
    )
    publish_assessment_event(
        event_type="QuizSubmitted",
        aggregate_id=attempt.id,
        correlation_id=correlation_id,
        payload={
            "assessment_id": str(attempt.quiz.assessment_id),
            "quiz_id": str(attempt.quiz_id),
            "course_id": str(attempt.quiz.assessment.course_id),
            "student_profile_id": str(attempt.student_profile_id),
            "attempt_number": attempt.attempt_number,
            "status": attempt.status,
            "score": str(total),
        },
    )
    return attempt


def attempt_deadline(attempt: QuizAttempt):
    candidates = []
    if attempt.quiz.time_limit_seconds:
        candidates.append(attempt.started_at + timedelta(seconds=attempt.quiz.time_limit_seconds))
    if attempt.quiz.assessment.available_until:
        candidates.append(attempt.quiz.assessment.available_until)
    return min(candidates) if candidates else None


def ordered_attempt_questions(attempt: QuizAttempt) -> list[Question]:
    order = _stored_question_order(attempt)
    links = list(attempt.quiz.question_links.select_related("question").all())
    links_by_question_id = {link.question_id: link for link in links}
    if order:
        ordered_links = [links_by_question_id[question_id] for question_id in order if question_id in links_by_question_id]
        ordered_links.extend([link for link in links if link.question_id not in order])
    else:
        ordered_links = links
    return [link.question for link in ordered_links]


def points_by_question(attempt: QuizAttempt) -> dict:
    return {
        link.question_id: link.points_override if link.points_override is not None else link.question.points
        for link in attempt.quiz.question_links.select_related("question")
    }


def score_answer(*, question: Question, answer_payload: dict[str, Any], link: QuizQuestion) -> Decimal | None:
    points = link.points_override if link.points_override is not None else question.points
    correct = question.correct_answer
    if question.question_type == QuestionType.MULTIPLE_CHOICE:
        expected = correct.get("choice_id") if isinstance(correct, dict) else correct
        actual = answer_payload.get("choice_id") if isinstance(answer_payload, dict) else None
        return points if str(actual) == str(expected) else Decimal("0")
    if question.question_type == QuestionType.MULTIPLE_SELECT:
        expected = correct.get("choice_ids") if isinstance(correct, dict) else correct
        actual = answer_payload.get("choice_ids") if isinstance(answer_payload, dict) else None
        if not isinstance(expected, list) or not isinstance(actual, list):
            return Decimal("0")
        return points if {str(item) for item in actual} == {str(item) for item in expected} else Decimal("0")
    if question.question_type == QuestionType.TRUE_FALSE:
        expected = correct.get("value") if isinstance(correct, dict) else correct
        actual = answer_payload.get("value") if isinstance(answer_payload, dict) else None
        return points if actual is expected else Decimal("0")
    if question.question_type == QuestionType.SHORT_ANSWER and isinstance(correct, dict):
        accepted = correct.get("accepted_answers") or []
        actual = str(answer_payload.get("text", "")).strip().lower() if isinstance(answer_payload, dict) else ""
        return points if actual in {str(item).strip().lower() for item in accepted} else Decimal("0")
    return None


def publish_assessment_event(
    *,
    event_type: str,
    aggregate_id,
    payload: dict[str, Any],
    correlation_id: str | None = None,
) -> dict[str, Any]:
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "aggregate_id": str(aggregate_id),
        "producer_service": settings.SERVICE_NAME,
        "timestamp": timezone.now().isoformat(),
        "version": 1,
        "correlation_id": correlation_id,
        "payload": payload,
    }
    logger.info("assessment_event %s", json.dumps(event, sort_keys=True))
    return event


def quiz_attempt_grading_source(attempt: QuizAttempt) -> dict[str, Any]:
    max_score = sum(points_by_question(attempt).values(), Decimal("0"))
    return {
        "submission_type": "quiz_attempt",
        "submission_id": attempt.id,
        "student_profile_id": attempt.student_profile_id,
        "course_id": attempt.quiz.assessment.course_id,
        "assessment_id": attempt.quiz.assessment_id,
        "score": str(attempt.score) if attempt.score is not None else None,
        "max_score": str(max_score),
        "status": attempt.status,
        "source_payload": {
            "attempt_number": attempt.attempt_number,
            "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
            "answer_count": attempt.answers.count(),
        },
    }


def assignment_submission_grading_source(submission: AssignmentSubmission) -> dict[str, Any]:
    return {
        "submission_type": "assignment_submission",
        "submission_id": submission.id,
        "student_profile_id": submission.student_profile_id,
        "course_id": submission.assignment.assessment.course_id,
        "assessment_id": submission.assignment.assessment_id,
        "score": None,
        "max_score": str(submission.assignment.max_points),
        "status": submission.status,
        "source_payload": {
            "submission_text": submission.submission_text,
            "attachment_asset_id": str(submission.attachment_asset_id) if submission.attachment_asset_id else None,
            "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
        },
    }


def _default_quiz_config(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "time_limit_seconds": config.get("time_limit_seconds"),
        "max_attempts": config.get("max_attempts"),
        "randomize_questions": config.get("randomize_questions", False),
        "auto_submit": config.get("auto_submit", True),
        "grading_policy": config.get("grading_policy", {}),
    }


def _default_assignment_config(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "due_at": config.get("due_at"),
        "allow_late_submission": config.get("allow_late_submission", False),
        "max_points": config.get("max_points", 0),
        "resource_asset_id": config.get("resource_asset_id"),
    }


def _validate_assessment_window(assessment: Assessment) -> None:
    now = timezone.now()
    if assessment.available_from and now < assessment.available_from:
        raise PermissionDenied("Assessment is not open yet.")
    if assessment.available_until and now > assessment.available_until:
        raise PermissionDenied("Assessment window has closed.")


def _validate_assignment_available(assignment: Assignment) -> None:
    assessment = assignment.assessment
    if (
        assessment.assessment_type != AssessmentType.ASSIGNMENT
        or assessment.status != AssessmentStatus.PUBLISHED
        or assessment.deleted_at is not None
    ):
        raise PermissionDenied("Assignment is not available.")
    now = timezone.now()
    if assessment.available_from and now < assessment.available_from:
        raise PermissionDenied("Assignment is not open yet.")
    if assessment.available_until and now > assessment.available_until:
        raise PermissionDenied("Assignment window has closed.")


def _finalize_assignment_submission(
    *,
    submission: AssignmentSubmission,
    actor_profile_id,
    correlation_id: str | None,
) -> AssignmentSubmission:
    if not submission.submission_text and not submission.attachment_asset_id:
        raise ValidationError({"submission": "Submission requires text or an attachment_asset_id."})
    now = timezone.now()
    assignment = submission.assignment
    late = bool(assignment.due_at and now > assignment.due_at)
    if late and not assignment.allow_late_submission:
        raise ValidationError({"due_at": "Late submissions are not allowed for this assignment."})
    submission.status = AssignmentSubmissionStatus.LATE if late else AssignmentSubmissionStatus.SUBMITTED
    submission.submitted_at = now
    submission.save(update_fields=["submission_text", "attachment_asset_id", "status", "submitted_at", "updated_at"])
    SubmissionAuditLog.objects.create(
        submission_type=SubmissionType.ASSIGNMENT_SUBMISSION,
        submission_id=submission.id,
        event_type="assignment_submitted_late" if late else "assignment_submitted",
        actor_profile_id=actor_profile_id,
        metadata={"assignment_id": str(assignment.id), "late": late},
    )
    publish_assessment_event(
        event_type="AssignmentSubmitted",
        aggregate_id=submission.id,
        correlation_id=correlation_id,
        payload={
            "assignment_id": str(assignment.id),
            "assessment_id": str(assignment.assessment_id),
            "course_id": str(assignment.assessment.course_id),
            "student_profile_id": str(submission.student_profile_id),
            "status": submission.status,
            "late": late,
        },
    )
    return submission


def _question_order_for_attempt(attempt: QuizAttempt) -> list:
    links = list(attempt.quiz.question_links.order_by("position", "id"))
    if attempt.quiz.randomize_questions:
        random.Random(str(attempt.id)).shuffle(links)
    return [link.question_id for link in links]


def _stored_question_order(attempt: QuizAttempt) -> list:
    log = (
        SubmissionAuditLog.objects.filter(
            submission_type=SubmissionType.QUIZ_ATTEMPT,
            submission_id=attempt.id,
            event_type="attempt_started",
        )
        .order_by("-created_at")
        .first()
    )
    if not log:
        return []
    return [uuid.UUID(value) for value in log.metadata.get("question_order", [])]
