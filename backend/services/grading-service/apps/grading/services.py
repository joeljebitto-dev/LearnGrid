from __future__ import annotations

import json
import logging
import secrets
import string
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any
from urllib import error, parse, request as urlrequest

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from learngrid_events import publish_event as publish_kafka_event
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError

from .models import (
    Certificate,
    CertificateEligibility,
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


class ProgressServiceError(APIException):
    status_code = 502
    default_code = "progress_service_error"
    default_detail = "Progress-service request failed."


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


def fetch_course_progress(*, token: str, student_profile_id, course_id) -> dict[str, Any] | None:
    data = _json_request(
        base_url=settings.PROGRESS_SERVICE_BASE_URL,
        path="/api/progress/courses/",
        token=token,
        query={"student_profile_id": student_profile_id, "course_id": course_id},
        error_class=ProgressServiceError,
    )
    if isinstance(data, list):
        return data[0] if data else None
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        return data["results"][0] if data["results"] else None
    raise ProgressServiceError("Progress-service response did not include course progress results.")


def validate_content_asset(*, token: str, asset_id) -> dict[str, Any]:
    if not asset_id:
        return {}
    return _json_request(
        base_url=settings.CONTENT_SERVICE_BASE_URL,
        path=f"/api/content/assets/{asset_id}/",
        token=token,
        error_class=ContentServiceError,
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


@transaction.atomic
def evaluate_certificate_eligibility(
    *,
    token: str,
    student_profile_id,
    course_id,
    certificate_asset_id=None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    if certificate_asset_id:
        validate_content_asset(token=token, asset_id=certificate_asset_id)

    threshold = certificate_pass_threshold(course_id=course_id)
    progress = fetch_course_progress(token=token, student_profile_id=student_profile_id, course_id=course_id)
    grade_percent = None
    eligible = False
    reason = "course_progress_missing"

    if progress:
        if not course_progress_complete(progress):
            reason = "course_incomplete"
        else:
            grade_percent = published_grade_percent(student_profile_id=student_profile_id, course_id=course_id)
            if grade_percent is None:
                reason = "published_results_missing"
            elif grade_percent < threshold:
                reason = "grade_below_threshold"
            else:
                eligible = True
                reason = "eligible"

    eligibility = upsert_certificate_eligibility(
        student_profile_id=student_profile_id,
        course_id=course_id,
        eligible=eligible,
        reason=reason,
    )
    certificate = None
    if eligible:
        certificate = issue_certificate(
            eligibility=eligibility,
            certificate_asset_id=certificate_asset_id,
        )
        publish_certificate_event(
            event_type="CertificateEligible",
            aggregate_id=eligibility.id,
            correlation_id=correlation_id,
            payload={
                "student_profile_id": str(student_profile_id),
                "course_id": str(course_id),
                "eligibility_id": str(eligibility.id),
                "certificate_id": str(certificate.id),
                "certificate_number": certificate.certificate_number,
                "grade_percent": str(grade_percent),
                "threshold_percent": str(threshold),
            },
        )
    return {
        "eligibility": eligibility,
        "certificate": certificate,
        "grade_percent": str(grade_percent) if grade_percent is not None else None,
        "threshold_percent": str(threshold),
    }


def certificate_pass_threshold(*, course_id) -> Decimal:
    for rule in GradingRule.objects.filter(course_id=course_id, assessment_id__isnull=True).order_by(
        "-updated_at",
        "-created_at",
    ):
        configuration = rule.configuration or {}
        if "certificate_min_percent" in configuration:
            value = _decimal_or_none(configuration.get("certificate_min_percent"))
            if value is not None:
                return value
    return Decimal(str(settings.GRADING_CERTIFICATE_DEFAULT_PASS_PERCENT))


def course_progress_complete(progress: dict[str, Any]) -> bool:
    if progress.get("status") == "completed":
        return True
    completion_percent = _decimal_or_none(progress.get("completion_percent")) or Decimal("0")
    return completion_percent >= Decimal("100")


def published_grade_percent(*, student_profile_id, course_id) -> Decimal | None:
    results = list(
        PublishedResult.objects.select_related("grade_record").filter(
            student_profile_id=student_profile_id,
            course_id=course_id,
        )
    )
    if not results:
        return None
    total_score = sum((result.published_score for result in results), Decimal("0"))
    total_max = sum((result.grade_record.max_score for result in results), Decimal("0"))
    if total_max <= 0:
        return None
    return ((total_score / total_max) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def upsert_certificate_eligibility(*, student_profile_id, course_id, eligible: bool, reason: str) -> CertificateEligibility:
    eligibility, _created = CertificateEligibility.objects.update_or_create(
        student_profile_id=student_profile_id,
        course_id=course_id,
        defaults={"eligible": eligible, "reason": reason},
    )
    return eligibility


def issue_certificate(*, eligibility: CertificateEligibility, certificate_asset_id=None) -> Certificate:
    certificate, created = Certificate.objects.get_or_create(
        certificate_eligibility=eligibility,
        defaults={
            "student_profile_id": eligibility.student_profile_id,
            "course_id": eligibility.course_id,
            "certificate_number": generate_certificate_number(),
            "certificate_asset_id": certificate_asset_id,
        },
    )
    if not created and certificate_asset_id and certificate.certificate_asset_id != certificate_asset_id:
        certificate.certificate_asset_id = certificate_asset_id
        certificate.save(update_fields=["certificate_asset_id"])
    return certificate


def update_certificate_asset(*, token: str, certificate: Certificate, certificate_asset_id) -> Certificate:
    if certificate_asset_id:
        validate_content_asset(token=token, asset_id=certificate_asset_id)
    certificate.certificate_asset_id = certificate_asset_id
    certificate.save(update_fields=["certificate_asset_id"])
    return certificate


def revoke_certificate(*, certificate: Certificate) -> Certificate:
    if certificate.revoked_at is None:
        certificate.revoked_at = timezone.now()
        certificate.save(update_fields=["revoked_at"])
    return certificate


def generate_certificate_number() -> str:
    alphabet = string.ascii_uppercase + string.digits
    issued_on = timezone.now().strftime("%Y%m%d")
    for _attempt in range(20):
        suffix = "".join(secrets.choice(alphabet) for _ in range(10))
        certificate_number = f"LG-{issued_on}-{suffix}"
        if not Certificate.objects.filter(certificate_number=certificate_number).exists():
            return certificate_number
    raise APIException("Could not generate a unique certificate number.")


def publish_certificate_event(
    *,
    event_type: str,
    aggregate_id,
    payload: dict[str, Any],
    correlation_id: str | None = None,
) -> dict[str, Any]:
    event = publish_kafka_event(
        event_type=event_type,
        aggregate_id=aggregate_id,
        producer_service=settings.SERVICE_NAME,
        correlation_id=correlation_id,
        payload=payload,
    )
    logger.info("certificate_event %s", json.dumps(event, sort_keys=True))
    return event


def _decimal_or_none(value) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


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
    event = publish_kafka_event(
        event_type=event_type,
        aggregate_id=aggregate_id,
        producer_service=settings.SERVICE_NAME,
        correlation_id=correlation_id,
        payload=payload,
    )
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
