from __future__ import annotations

import uuid

from django.db import models


class GradingRuleType(models.TextChoices):
    POINTS = "points", "Points"
    PERCENTAGE = "percentage", "Percentage"
    WEIGHTED = "weighted", "Weighted"
    PASS_FAIL = "pass_fail", "Pass/fail"


class GradeRecordStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    CALCULATED = "calculated", "Calculated"
    REVIEWED = "reviewed", "Reviewed"
    PUBLISHED = "published", "Published"
    OVERRIDDEN = "overridden", "Overridden"


class ManualReviewStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IN_REVIEW = "in_review", "In review"
    COMPLETED = "completed", "Completed"
    RETURNED = "returned", "Returned"


class GradingRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course_id = models.UUIDField()
    assessment_id = models.UUIDField(null=True, blank=True)
    rule_type = models.CharField(max_length=32, choices=GradingRuleType.choices)
    configuration = models.JSONField(default=dict)
    created_by_profile_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grading_rules"
        indexes = [
            models.Index(fields=["course_id"], name="idx_grules_course_id"),
            models.Index(fields=["assessment_id"], name="idx_grules_assessment_id"),
        ]

    def __str__(self) -> str:
        return f"{self.course_id}:{self.rule_type}"


class GradeRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_profile_id = models.UUIDField()
    course_id = models.UUIDField()
    assessment_id = models.UUIDField(null=True, blank=True)
    submission_id = models.UUIDField(null=True, blank=True)
    score = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    max_score = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(
        max_length=24,
        choices=GradeRecordStatus.choices,
        default=GradeRecordStatus.DRAFT,
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grade_records"
        indexes = [
            models.Index(fields=["student_profile_id", "course_id"], name="idx_grade_student_course"),
            models.Index(fields=["assessment_id", "status"], name="idx_grade_assess_status"),
            models.Index(fields=["course_id", "status"], name="idx_grade_course_status"),
            models.Index(fields=["submission_id"], name="idx_grade_submission_id"),
        ]

    def __str__(self) -> str:
        return f"{self.student_profile_id}:{self.course_id}:{self.score}/{self.max_score}"


class ManualReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grade_record = models.ForeignKey(
        GradeRecord,
        on_delete=models.CASCADE,
        related_name="manual_reviews",
    )
    reviewer_profile_id = models.UUIDField()
    status = models.CharField(
        max_length=24,
        choices=ManualReviewStatus.choices,
        default=ManualReviewStatus.PENDING,
    )
    feedback = models.TextField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "manual_reviews"
        indexes = [
            models.Index(fields=["grade_record"], name="idx_reviews_grade_record"),
            models.Index(fields=["reviewer_profile_id", "status"], name="idx_reviews_reviewer_status"),
        ]


class GradeHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grade_record = models.ForeignKey(
        GradeRecord,
        on_delete=models.CASCADE,
        related_name="history",
    )
    previous_score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    new_score = models.DecimalField(max_digits=8, decimal_places=2)
    changed_by_profile_id = models.UUIDField(null=True, blank=True)
    change_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "grade_history"
        indexes = [
            models.Index(fields=["grade_record"], name="idx_grade_history_record"),
        ]


class PublishedResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grade_record = models.OneToOneField(
        GradeRecord,
        on_delete=models.CASCADE,
        related_name="published_result",
    )
    student_profile_id = models.UUIDField()
    course_id = models.UUIDField()
    published_score = models.DecimalField(max_digits=8, decimal_places=2)
    published_feedback = models.TextField(null=True, blank=True)
    published_by_profile_id = models.UUIDField()
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "published_results"
        constraints = [
            models.UniqueConstraint(fields=["grade_record"], name="uq_pub_results_grade_record"),
        ]
        indexes = [
            models.Index(fields=["student_profile_id", "course_id"], name="idx_pub_results_student_course"),
        ]


class CertificateEligibility(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_profile_id = models.UUIDField()
    course_id = models.UUIDField()
    eligible = models.BooleanField(default=False)
    reason = models.TextField(null=True, blank=True)
    evaluated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "certificate_eligibility"
        constraints = [
            models.UniqueConstraint(
                fields=["student_profile_id", "course_id"],
                name="uq_cert_elig_student_course",
            ),
        ]
        indexes = [
            models.Index(fields=["course_id", "eligible"], name="idx_cert_elig_course_eligible"),
        ]


class Certificate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    certificate_eligibility = models.OneToOneField(
        CertificateEligibility,
        on_delete=models.CASCADE,
        related_name="certificate",
    )
    student_profile_id = models.UUIDField()
    course_id = models.UUIDField()
    certificate_number = models.CharField(max_length=80, unique=True)
    certificate_asset_id = models.UUIDField(null=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "certificates"
        constraints = [
            models.UniqueConstraint(
                fields=["certificate_eligibility"],
                name="uq_certificates_eligibility",
            ),
        ]
        indexes = [
            models.Index(fields=["student_profile_id", "course_id"], name="idx_certs_student_course"),
        ]
