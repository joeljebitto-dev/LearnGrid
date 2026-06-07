from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import (
    AccessGrant,
    AccessGrantStatus,
    BatchEnrollment,
    CohortEnrollment,
    Enrollment,
    EnrollmentHistory,
    EnrollmentJobStatus,
    EnrollmentStatus,
)


logger = logging.getLogger(__name__)


def create_enrollment(*, validated_data: dict[str, Any], correlation_id: str | None = None) -> Enrollment:
    try:
        with transaction.atomic():
            enrollment = Enrollment.objects.create(**validated_data)
            EnrollmentHistory.objects.create(
                enrollment=enrollment,
                from_status=None,
                to_status=enrollment.status,
                changed_by_profile_id=enrollment.enrolled_by_profile_id,
                reason="Enrollment created",
            )
            sync_access_grant(enrollment)
    except IntegrityError as exc:
        raise ValidationError({"student_profile_id": "Student is already enrolled in this course."}) from exc
    publish_enrollment_event(
        event_type="StudentEnrolled",
        aggregate_id=enrollment.id,
        correlation_id=correlation_id,
        payload={
            "student_profile_id": str(enrollment.student_profile_id),
            "course_id": str(enrollment.course_id),
            "institution_id": str(enrollment.institution_id),
            "status": enrollment.status,
        },
    )
    return enrollment


def transition_enrollment(
    *,
    enrollment: Enrollment,
    to_status: str,
    changed_by_profile_id=None,
    reason: str | None = None,
    correlation_id: str | None = None,
) -> Enrollment:
    from_status = enrollment.status
    enrollment.status = to_status
    if to_status == EnrollmentStatus.COMPLETED:
        enrollment.completed_at = timezone.now()
    enrollment.save()
    EnrollmentHistory.objects.create(
        enrollment=enrollment,
        from_status=from_status,
        to_status=to_status,
        changed_by_profile_id=changed_by_profile_id,
        reason=reason,
    )
    sync_access_grant(enrollment)
    if to_status in {EnrollmentStatus.CANCELLED, EnrollmentStatus.SUSPENDED}:
        event_type = "StudentRemovedFromCourse"
    elif to_status == EnrollmentStatus.EXPIRED:
        event_type = "CourseAccessExpired"
    else:
        event_type = "EnrollmentStatusChanged"
    publish_enrollment_event(
        event_type=event_type,
        aggregate_id=enrollment.id,
        correlation_id=correlation_id,
        payload={
            "student_profile_id": str(enrollment.student_profile_id),
            "course_id": str(enrollment.course_id),
            "institution_id": str(enrollment.institution_id),
            "from_status": from_status,
            "to_status": to_status,
        },
    )
    return enrollment


def sync_access_grant(enrollment: Enrollment) -> None:
    grant, _created = AccessGrant.objects.get_or_create(
        enrollment=enrollment,
        student_profile_id=enrollment.student_profile_id,
        course_id=enrollment.course_id,
        defaults={"valid_until": enrollment.expires_at},
    )
    if enrollment.status == EnrollmentStatus.ACTIVE:
        grant.access_status = AccessGrantStatus.ACTIVE
    elif enrollment.status == EnrollmentStatus.EXPIRED:
        grant.access_status = AccessGrantStatus.EXPIRED
        grant.valid_until = grant.valid_until or timezone.now()
    elif enrollment.status == EnrollmentStatus.SUSPENDED:
        grant.access_status = AccessGrantStatus.SUSPENDED
    else:
        grant.access_status = AccessGrantStatus.REVOKED
        grant.valid_until = grant.valid_until or timezone.now()
    grant.save()


def has_active_access(*, student_profile_id, course_id) -> bool:
    now = timezone.now()
    return AccessGrant.objects.filter(
        student_profile_id=student_profile_id,
        course_id=course_id,
        access_status=AccessGrantStatus.ACTIVE,
    ).filter(valid_until__isnull=True).exists() or AccessGrant.objects.filter(
        student_profile_id=student_profile_id,
        course_id=course_id,
        access_status=AccessGrantStatus.ACTIVE,
        valid_until__gt=now,
    ).exists()


def create_batch_enrollment_job(*, validated_data: dict[str, Any]) -> BatchEnrollment:
    student_ids = validated_data.pop("student_profile_ids", [])
    institution_id = validated_data.pop("institution_id")
    job = BatchEnrollment.objects.create(status=EnrollmentJobStatus.PROCESSING, **validated_data)
    summary = _create_many_enrollments(
        student_profile_ids=student_ids,
        course_id=job.course_id,
        institution_id=institution_id,
        requested_by_profile_id=job.requested_by_profile_id,
    )
    job.status = EnrollmentJobStatus.COMPLETED if summary["failed"] == 0 else EnrollmentJobStatus.FAILED
    job.summary = summary
    job.save()
    return job


def create_cohort_enrollment_job(*, validated_data: dict[str, Any]) -> CohortEnrollment:
    student_ids = validated_data.pop("student_profile_ids", [])
    institution_id = validated_data.pop("institution_id")
    job = CohortEnrollment.objects.create(status=EnrollmentJobStatus.PROCESSING, **validated_data)
    summary = _create_many_enrollments(
        student_profile_ids=student_ids,
        course_id=job.course_id,
        institution_id=institution_id,
        requested_by_profile_id=job.requested_by_profile_id,
    )
    job.status = EnrollmentJobStatus.COMPLETED if summary["failed"] == 0 else EnrollmentJobStatus.FAILED
    job.summary = summary
    job.save()
    return job


def _create_many_enrollments(*, student_profile_ids, course_id, institution_id, requested_by_profile_id) -> dict:
    created = 0
    failures = []
    for student_profile_id in student_profile_ids:
        try:
            create_enrollment(
                validated_data={
                    "student_profile_id": student_profile_id,
                    "course_id": course_id,
                    "institution_id": institution_id,
                    "enrolled_by_profile_id": requested_by_profile_id,
                }
            )
            created += 1
        except ValidationError as exc:
            failures.append({"student_profile_id": str(student_profile_id), "error": str(exc.detail)})
    return {"requested": len(student_profile_ids), "created": created, "failed": len(failures), "failures": failures}


def publish_enrollment_event(
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
    logger.info("enrollment_event %s", json.dumps(event, sort_keys=True))
    return event
