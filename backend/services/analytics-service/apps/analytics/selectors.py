from __future__ import annotations

from uuid import UUID

from django.db.models import QuerySet

from .models import DashboardAggregate, DashboardScopeType, ReportSnapshot


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
