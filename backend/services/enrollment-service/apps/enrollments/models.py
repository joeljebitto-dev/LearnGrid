from __future__ import annotations

import uuid

from django.db import models
from django.db.models import Q


class EnrollmentStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    EXPIRED = "expired", "Expired"
    CANCELLED = "cancelled", "Cancelled"
    SUSPENDED = "suspended", "Suspended"


class EnrollmentJobStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class AccessGrantStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    SUSPENDED = "suspended", "Suspended"
    REVOKED = "revoked", "Revoked"


class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_profile_id = models.UUIDField()
    course_id = models.UUIDField()
    institution_id = models.UUIDField()
    status = models.CharField(
        max_length=24,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.ACTIVE,
    )
    enrolled_by_profile_id = models.UUIDField(null=True, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "enrollments"
        constraints = [
            models.UniqueConstraint(
                fields=["student_profile_id", "course_id"],
                name="uq_enrollments_student_course",
            ),
        ]
        indexes = [
            models.Index(fields=["course_id", "status"], name="idx_enroll_course_status"),
            models.Index(fields=["student_profile_id", "status"], name="idx_enroll_student_status"),
            models.Index(fields=["institution_id"], name="idx_enroll_institution_id"),
        ]


class BatchEnrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch_id = models.UUIDField()
    course_id = models.UUIDField()
    requested_by_profile_id = models.UUIDField()
    status = models.CharField(
        max_length=24,
        choices=EnrollmentJobStatus.choices,
        default=EnrollmentJobStatus.QUEUED,
    )
    summary = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "batch_enrollments"
        indexes = [
            models.Index(fields=["batch_id", "course_id"], name="idx_batch_enroll_batch_course"),
            models.Index(fields=["status"], name="idx_batch_enroll_status"),
        ]


class CohortEnrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cohort_id = models.UUIDField()
    course_id = models.UUIDField()
    requested_by_profile_id = models.UUIDField()
    status = models.CharField(
        max_length=24,
        choices=EnrollmentJobStatus.choices,
        default=EnrollmentJobStatus.QUEUED,
    )
    summary = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cohort_enrollments"
        indexes = [
            models.Index(fields=["cohort_id", "course_id"], name="idx_cohort_enroll_course"),
            models.Index(fields=["status"], name="idx_cohort_enroll_status"),
        ]


class EnrollmentHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="history",
    )
    from_status = models.CharField(max_length=24, null=True, blank=True)
    to_status = models.CharField(max_length=24)
    changed_by_profile_id = models.UUIDField(null=True, blank=True)
    reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "enrollment_history"
        indexes = [
            models.Index(fields=["enrollment"], name="idx_enroll_history_enroll"),
            models.Index(fields=["created_at"], name="idx_enroll_history_created"),
        ]


class AccessGrant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="access_grants",
    )
    student_profile_id = models.UUIDField()
    course_id = models.UUIDField()
    access_status = models.CharField(
        max_length=24,
        choices=AccessGrantStatus.choices,
        default=AccessGrantStatus.ACTIVE,
    )
    valid_from = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "access_grants"
        constraints = [
            models.UniqueConstraint(
                fields=["student_profile_id", "course_id"],
                condition=Q(access_status=AccessGrantStatus.ACTIVE),
                name="uq_active_access_grant",
            ),
        ]
        indexes = [
            models.Index(
                fields=["student_profile_id", "course_id"], name="idx_access_student_course"
            ),
            models.Index(fields=["course_id", "access_status"], name="idx_access_course_status"),
        ]
