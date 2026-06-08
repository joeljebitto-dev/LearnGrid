import uuid

from django.db import models
from django.utils import timezone


class DashboardScopeType(models.TextChoices):
    STUDENT = "student", "Student"
    INSTRUCTOR = "instructor", "Instructor"
    INSTITUTION = "institution", "Institution"
    COURSE = "course", "Course"
    PLATFORM = "platform", "Platform"


class ReportType(models.TextChoices):
    ACTIVE_USERS = "active_users", "Active users"
    ENROLLMENTS = "enrollments", "Enrollments"
    COMPLETION_RATES = "completion_rates", "Completion rates"
    ASSESSMENT_RESULTS = "assessment_results", "Assessment results"
    SYSTEM_USAGE = "system_usage", "System usage"
    DASHBOARD = "dashboard", "Dashboard"


class SearchResourceType(models.TextChoices):
    COURSE = "course", "Course"
    USER = "user", "User"
    ENROLLMENT = "enrollment", "Enrollment"
    ASSESSMENT = "assessment", "Assessment"
    SUBMISSION = "submission", "Submission"


class EventFact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.UUIDField(unique=True)
    event_type = models.CharField(max_length=80)
    producer_service = models.CharField(max_length=80)
    aggregate_id = models.UUIDField()
    institution_id = models.UUIDField(null=True, blank=True)
    occurred_at = models.DateTimeField()
    payload = models.JSONField(default=dict)
    ingested_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "event_facts"
        indexes = [
            models.Index(fields=["event_type", "occurred_at"], name="idx_event_facts_type_time"),
            models.Index(
                fields=["institution_id", "occurred_at"],
                name="idx_event_facts_inst_time",
            ),
            models.Index(fields=["aggregate_id"], name="idx_event_facts_aggregate_id"),
        ]


class DashboardAggregate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scope_type = models.CharField(max_length=32, choices=DashboardScopeType.choices)
    scope_id = models.UUIDField()
    metric_date = models.DateField()
    metrics = models.JSONField(default=dict)
    computed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "dashboard_aggregates"
        constraints = [
            models.UniqueConstraint(
                fields=["scope_type", "scope_id", "metric_date"],
                name="uq_dash_aggr_scope_date",
            )
        ]
        indexes = [models.Index(fields=["scope_type"], name="idx_dash_aggr_scope_type")]


class ReportSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution_id = models.UUIDField(null=True, blank=True)
    report_type = models.CharField(max_length=80, choices=ReportType.choices)
    parameters = models.JSONField(default=dict)
    result_payload = models.JSONField(default=dict)
    generated_by_profile_id = models.UUIDField(null=True, blank=True)
    generated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "report_snapshots"
        indexes = [
            models.Index(
                fields=["institution_id", "report_type"],
                name="idx_report_snap_inst_type",
            ),
            models.Index(fields=["generated_at"], name="idx_report_snap_generated"),
        ]


class UsageMetric(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_name = models.CharField(max_length=128)
    metric_value = models.DecimalField(max_digits=18, decimal_places=4)
    scope_type = models.CharField(max_length=32, null=True, blank=True)
    scope_id = models.UUIDField(null=True, blank=True)
    bucket_start_at = models.DateTimeField()
    bucket_end_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "usage_metrics"
        indexes = [
            models.Index(
                fields=["metric_name", "bucket_start_at"],
                name="idx_usage_metrics_name_bucket",
            ),
            models.Index(
                fields=["scope_type", "scope_id", "bucket_start_at"],
                name="idx_usage_metrics_scope_bucket",
            ),
        ]


class SearchIndexRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resource_type = models.CharField(max_length=64, choices=SearchResourceType.choices)
    resource_id = models.UUIDField()
    institution_id = models.UUIDField(null=True, blank=True)
    search_text = models.TextField()
    metadata = models.JSONField(default=dict)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "search_index_records"
        constraints = [
            models.UniqueConstraint(
                fields=["resource_type", "resource_id"],
                name="uq_search_index_resource",
            )
        ]
        indexes = [
            models.Index(fields=["resource_type"], name="idx_search_index_resource_type"),
            models.Index(fields=["institution_id"], name="idx_search_index_institution"),
        ]
