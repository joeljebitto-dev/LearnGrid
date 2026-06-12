from __future__ import annotations

from uuid import UUID

from django.db.models import QuerySet

from .models import (
    DashboardAggregate,
    DashboardScopeType,
    ReportSnapshot,
    SearchIndexRecord,
    UsageMetric,
)


PLATFORM_SCOPE_ID = UUID("00000000-0000-0000-0000-000000000000")


STUDENT_DEFAULT_METRICS = {
    "active_courses": [],
    "completed_lessons": [],
    "pending_assessments": [],
    "grades": [],
    "upcoming_deadlines": [],
    "summary": {
        "active_course_count": 0,
        "completed_lesson_count": 0,
        "pending_assessment_count": 0,
        "grade_count": 0,
        "upcoming_deadline_count": 0,
    },
}

INSTRUCTOR_DEFAULT_METRICS = {
    "learner_engagement": [],
    "progress_distribution": [],
    "assessment_status": [],
    "course_summaries": [],
    "summary": {
        "assigned_course_count": 0,
        "active_learner_count": 0,
        "pending_assessment_count": 0,
        "average_progress_percent": 0,
    },
}

ADMIN_DEFAULT_METRICS = {
    "active_users": [],
    "enrollments": [],
    "completion_rates": [],
    "assessment_results": [],
    "system_usage": [],
    "summary": {
        "active_user_count": 0,
        "enrollment_count": 0,
        "average_completion_percent": 0,
        "assessment_result_count": 0,
        "system_event_count": 0,
    },
}


def latest_dashboard_aggregate(
    *,
    scope_type: str,
    scope_id,
) -> DashboardAggregate | None:
    return (
        DashboardAggregate.objects.filter(scope_type=scope_type, scope_id=scope_id)
        .order_by("-metric_date", "-computed_at")
        .first()
    )


def _merge_metrics(defaults: dict, metrics: dict | None) -> dict:
    merged = {key: value for key, value in defaults.items()}
    for key, value in (metrics or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            nested = dict(merged[key])
            nested.update(value)
            merged[key] = nested
        else:
            merged[key] = value
    return merged


def dashboard_payload(
    *,
    portal: str,
    scope_type: str,
    scope_id,
    profile: dict | None = None,
    institution_id=None,
) -> dict:
    defaults_by_portal = {
        "student": STUDENT_DEFAULT_METRICS,
        "instructor": INSTRUCTOR_DEFAULT_METRICS,
        "admin": ADMIN_DEFAULT_METRICS,
    }
    aggregate = latest_dashboard_aggregate(scope_type=scope_type, scope_id=scope_id)
    metrics = _merge_metrics(defaults_by_portal[portal], aggregate.metrics if aggregate else {})
    return {
        "portal": portal,
        "profile": profile,
        "institution_id": str(institution_id) if institution_id else None,
        "aggregate": {
            "id": str(aggregate.id),
            "metric_date": aggregate.metric_date.isoformat(),
            "computed_at": aggregate.computed_at.isoformat(),
        }
        if aggregate
        else None,
        **metrics,
    }


def report_snapshots(filters: dict) -> QuerySet[ReportSnapshot]:
    queryset = ReportSnapshot.objects.order_by("-generated_at", "-id")
    if "institution_id" in filters:
        queryset = queryset.filter(institution_id=filters.get("institution_id"))
    if report_type := filters.get("report_type"):
        queryset = queryset.filter(report_type=report_type)
    return queryset


def platform_dashboard_payload(profile: dict | None = None) -> dict:
    return dashboard_payload(
        portal="admin",
        scope_type=DashboardScopeType.PLATFORM,
        scope_id=PLATFORM_SCOPE_ID,
        profile=profile,
    )


def search_index_records(
    filters: dict, *, resource_type: str | None = None
) -> QuerySet[SearchIndexRecord]:
    queryset = SearchIndexRecord.objects.order_by("-updated_at", "-id")
    selected_resource_type = resource_type or filters.get("resource_type")
    if selected_resource_type:
        queryset = queryset.filter(resource_type=selected_resource_type)
    if "institution_id" in filters:
        queryset = queryset.filter(institution_id=filters.get("institution_id"))
    if q := filters.get("q"):
        queryset = queryset.filter(search_text__icontains=q)

    metadata_filters = {
        "status": "status",
        "course_id": "course_id",
        "profile_type": "profile_type",
        "assessment_type": "assessment_type",
        "submission_status": "submission_status",
    }
    for filter_key, metadata_key in metadata_filters.items():
        if value := filters.get(filter_key):
            queryset = queryset.filter(**{f"metadata__{metadata_key}": str(value)})

    sort = filters.get("sort") or "-updated_at"
    allowed_sorts = {"updated_at", "-updated_at", "resource_type"}
    if sort in allowed_sorts:
        queryset = queryset.order_by(sort, "-id")
    return queryset


def dashboard_aggregates(filters: dict) -> QuerySet[DashboardAggregate]:
    queryset = DashboardAggregate.objects.order_by("-metric_date", "-computed_at", "-id")
    if scope_type := filters.get("scope_type"):
        queryset = queryset.filter(scope_type=scope_type)
    if scope_id := filters.get("scope_id"):
        queryset = queryset.filter(scope_id=scope_id)
    if institution_id := filters.get("institution_id"):
        queryset = queryset.filter(
            scope_type=DashboardScopeType.INSTITUTION, scope_id=institution_id
        )
    if metric_date := filters.get("metric_date"):
        queryset = queryset.filter(metric_date=metric_date)
    sort = filters.get("sort") or "-metric_date"
    allowed_sorts = {"metric_date", "-metric_date", "computed_at", "-computed_at"}
    if sort in allowed_sorts:
        queryset = queryset.order_by(sort, "-id")
    return queryset


def usage_metrics(filters: dict) -> QuerySet[UsageMetric]:
    queryset = UsageMetric.objects.order_by("-bucket_start_at", "-id")
    if metric_name := filters.get("metric_name"):
        queryset = queryset.filter(metric_name=metric_name)
    if scope_type := filters.get("scope_type"):
        queryset = queryset.filter(scope_type=scope_type)
    if scope_id := filters.get("scope_id"):
        queryset = queryset.filter(scope_id=scope_id)
    if bucket_start_at := filters.get("bucket_start_at"):
        queryset = queryset.filter(bucket_start_at__gte=bucket_start_at)
    if bucket_end_at := filters.get("bucket_end_at"):
        queryset = queryset.filter(bucket_end_at__lte=bucket_end_at)
    sort = filters.get("sort") or "-bucket_start_at"
    allowed_sorts = {"bucket_start_at", "-bucket_start_at", "metric_name"}
    if sort in allowed_sorts:
        queryset = queryset.order_by(sort, "-id")
    return queryset
