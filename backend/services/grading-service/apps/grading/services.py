from __future__ import annotations

import json
import logging
import uuid
from decimal import Decimal
from typing import Any
from urllib import error, parse, request as urlrequest

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError

from .models import (
    GradeHistory,
    GradeRecord,
    GradeRecordStatus,
    GradingRule,
    ManualReview,
    ManualReviewStatus,
    PublishedResult,
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


class AssessmentServiceError(APIException):
    status_code = 502
    default_code = "assessment_service_error"
    default_detail = "Assessment-service request failed."


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
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urlrequest.Request(
        url,
        data=body,
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
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        if exc.code == 404:
            raise NotFound("Remote resource was not found.") from exc
        if exc.code in {401, 403}:
            raise PermissionDenied("Remote service denied access.") from exc
        raise error_class(f"Remote service returned HTTP {exc.code}.") from exc
    except (error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise error_class("Remote service is unavailable.") from exc


def current_profile(*, token: str) -> dict[str, Any]:
    return _json_request(
        base_url=settings.USER_SERVICE_BASE_URL,
        path="/api/users/profiles/me/",
        token=token,
        error_class=UserServiceError,
    )


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


def fetch_grading_source(*, token: str, submission_type: str, submission_id) -> dict[str, Any]:
    if submission_type == "quiz_attempt":
        path = f"/api/assessments/grading/quiz-attempts/{submission_id}/"
    elif submission_type == "assignment_submission":
        path = f"/api/assessments/grading/assignment-submissions/{submission_id}/"
    else:
        raise ValidationError({"submission_type": "Unsupported submission type."})
    return _json_request(
        base_url=settings.ASSESSMENT_SERVICE_BASE_URL,
        path=path,
        token=token,
        error_class=AssessmentServiceError,
    )


def mark_assignment_submission_graded(*, token: str, submission_id, grade_record_id) -> dict[str, Any]:
    return _json_request(
        base_url=settings.ASSESSMENT_SERVICE_BASE_URL,
        path=f"/api/assessments/submissions/{submission_id}/mark-graded/",
        token=token,
        method="POST",
        payload={"grade_record_id": str(grade_record_id)},
        error_class=AssessmentServiceError,
    )


def create_grading_rule(*, validated_data: dict[str, Any]) -> GradingRule:
    return GradingRule.objects.create(**validated_data)


def update_grading_rule(*, rule: GradingRule, validated_data: dict[str, Any]) -> GradingRule:
    for field in ["assessment_id", "rule_type", "configuration"]:
        if field in validated_data:
            setattr(rule, field, validated_data[field])
    rule.save()
    return rule


@transaction.atomic
def calculate_grade_from_quiz(
    *,
    source: dict[str, Any],
    changed_by_profile_id,
    correlation_id: str | None = None,
) -> GradeRecord:
    if source["submission_type"] != "quiz_attempt":
        raise ValidationError({"submission_type": "Automated calculation only supports quiz attempts."})
    grade_record = upsert_grade_record(
        source=source,
        score=Decimal(str(source.get("score") or "0")),
        max_score=Decimal(str(source["max_score"])),
        status=GradeRecordStatus.CALCULATED,
        changed_by_profile_id=changed_by_profile_id,
        change_reason="Automated objective quiz calculation",
    )
    publish_grade_event(
        event_type="GradeCalculated",
        aggregate_id=grade_record.id,
        correlation_id=correlation_id,
        payload=_grade_event_payload(grade_record),
    )
    return grade_record


@transaction.atomic
def create_manual_review(*, source: dict[str, Any], reviewer_profile_id) -> ManualReview:
    grade_record = upsert_grade_record(
        source=source,
        score=Decimal(str(source.get("score") or "0")),
        max_score=Decimal(str(source["max_score"])),
        status=GradeRecordStatus.DRAFT,
        changed_by_profile_id=reviewer_profile_id,
        change_reason="Manual review created",
    )
    review = ManualReview.objects.create(
        grade_record=grade_record,
        reviewer_profile_id=reviewer_profile_id,
        status=ManualReviewStatus.PENDING,
    )
    return review


@transaction.atomic
def complete_manual_review(*, review: ManualReview, score, feedback: str | None) -> GradeRecord:
    previous_score = review.grade_record.score
    review.status = ManualReviewStatus.COMPLETED
    review.feedback = feedback
    review.reviewed_at = timezone.now()
    review.save()
    grade_record = review.grade_record
    grade_record.score = score
    grade_record.status = GradeRecordStatus.REVIEWED
    grade_record.save(update_fields=["score", "status", "updated_at"])
    GradeHistory.objects.create(
        grade_record=grade_record,
        previous_score=previous_score,
        new_score=score,
        changed_by_profile_id=review.reviewer_profile_id,
        change_reason="Manual review completed",
    )
    return grade_record


@transaction.atomic
def override_grade(*, grade_record: GradeRecord, score, max_score=None, changed_by_profile_id, reason: str) -> GradeRecord:
    if not reason.strip():
        raise ValidationError({"change_reason": "Override reason is required."})
    previous_score = grade_record.score
    grade_record.score = score
    if max_score is not None:
        grade_record.max_score = max_score
    grade_record.status = GradeRecordStatus.OVERRIDDEN
    grade_record.save(update_fields=["score", "max_score", "status", "updated_at"])
    GradeHistory.objects.create(
        grade_record=grade_record,
        previous_score=previous_score,
        new_score=score,
        changed_by_profile_id=changed_by_profile_id,
        change_reason=reason,
    )
    return grade_record


@transaction.atomic
def publish_grade(
    *,
    grade_record: GradeRecord,
    published_by_profile_id,
    feedback: str | None,
    token: str,
    correlation_id: str | None = None,
) -> PublishedResult:
    if grade_record.status == GradeRecordStatus.PUBLISHED:
        if hasattr(grade_record, "published_result"):
            return grade_record.published_result
    grade_record.status = GradeRecordStatus.PUBLISHED
    grade_record.published_at = timezone.now()
    grade_record.save(update_fields=["status", "published_at", "updated_at"])
    result, _created = PublishedResult.objects.get_or_create(
        grade_record=grade_record,
        defaults={
            "student_profile_id": grade_record.student_profile_id,
            "course_id": grade_record.course_id,
            "published_score": grade_record.score,
            "published_feedback": feedback,
            "published_by_profile_id": published_by_profile_id,
        },
    )
    if grade_record.submission_id:
        try:
            mark_assignment_submission_graded(
                token=token,
                submission_id=grade_record.submission_id,
                grade_record_id=grade_record.id,
            )
        except APIException:
            pass
    publish_grade_event(
        event_type="GradePublished",
        aggregate_id=grade_record.id,
        correlation_id=correlation_id,
        payload=_grade_event_payload(grade_record),
    )
    return result


def upsert_grade_record(
    *,
    source: dict[str, Any],
    score,
    max_score,
    status: str,
    changed_by_profile_id,
    change_reason: str,
) -> GradeRecord:
    grade_record, created = GradeRecord.objects.get_or_create(
        submission_id=source["submission_id"],
        defaults={
            "student_profile_id": source["student_profile_id"],
            "course_id": source["course_id"],
            "assessment_id": source.get("assessment_id"),
            "score": score,
            "max_score": max_score,
            "status": status,
        },
    )
    previous_score = None if created else grade_record.score
    if not created:
        grade_record.student_profile_id = source["student_profile_id"]
        grade_record.course_id = source["course_id"]
        grade_record.assessment_id = source.get("assessment_id")
        grade_record.score = score
        grade_record.max_score = max_score
        grade_record.status = status
        grade_record.save()
    GradeHistory.objects.create(
        grade_record=grade_record,
        previous_score=previous_score,
        new_score=score,
        changed_by_profile_id=changed_by_profile_id,
        change_reason=change_reason,
    )
    return grade_record


def publish_grade_event(
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
    logger.info("grade_event %s", json.dumps(event, sort_keys=True))
    return event


def _grade_event_payload(grade_record: GradeRecord) -> dict[str, Any]:
    return {
        "student_profile_id": str(grade_record.student_profile_id),
        "course_id": str(grade_record.course_id),
        "assessment_id": str(grade_record.assessment_id) if grade_record.assessment_id else None,
        "submission_id": str(grade_record.submission_id) if grade_record.submission_id else None,
        "score": str(grade_record.score),
        "max_score": str(grade_record.max_score),
        "status": grade_record.status,
    }
