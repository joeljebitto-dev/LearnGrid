from __future__ import annotations

import json
from collections import Counter
from datetime import timezone as dt_timezone
from decimal import Decimal
from typing import Any
from urllib import error, request as urlrequest

import redis
from django.conf import settings
from django.db import transaction
from django.db.models import Avg
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from learngrid_redis import RedisKeyBuilder
from learngrid_redis import get_json_cache
from learngrid_redis import redis_client
from learngrid_redis import set_json_cache
from learngrid_events import DuplicateEvent
from learngrid_events import publish_event as publish_kafka_event
from rest_framework.exceptions import APIException, NotFound, PermissionDenied

from .models import (
    DashboardAggregate,
    DashboardScopeType,
    EventFact,
    ReportSnapshot,
    ReportType,
    SearchIndexRecord,
    SearchResourceType,
    UsageMetric,
)
from .permissions import remote_authorization_check
from .selectors import PLATFORM_SCOPE_ID, dashboard_payload


SEARCH_PERMISSION_BY_RESOURCE: dict[str, str] = {
    SearchResourceType.COURSE: "course.view",
    SearchResourceType.USER: "profile.view",
    SearchResourceType.ENROLLMENT: "enrollment.view",
    SearchResourceType.ASSESSMENT: "assessment.view",
    SearchResourceType.SUBMISSION: "submission.view",
}


class UserServiceError(APIException):
    status_code = 502
    default_code = "user_service_error"
    default_detail = "User-service request failed."


def auth_token(request) -> str:
    return str(request.auth)


def current_profile(*, token: str) -> dict[str, Any]:
    request = urlrequest.Request(
        f"{settings.USER_SERVICE_BASE_URL.rstrip('/')}/api/users/profiles/me/",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="GET",
    )
    try:
        with urlrequest.urlopen(request, timeout=3) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        if exc.code == 404:
            raise NotFound("No profile exists for the authenticated account.") from exc
        if exc.code in {401, 403}:
            raise PermissionDenied("Profile lookup was denied.") from exc
        raise UserServiceError(f"User-service returned HTTP {exc.code}.") from exc
    except (error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise UserServiceError("User-service is unavailable.") from exc


def require_analytics_view(
    *,
    token: str,
    institution_id: str | None = None,
    platform: bool = False,
) -> None:
    scope_type = "platform" if platform or not institution_id else "institution"
    scope_id = None if scope_type == "platform" else str(institution_id)
    if not remote_authorization_check(
        token=token,
        permission="analytics.view",
        scope_type=scope_type,
        scope_id=scope_id,
    ):
        raise PermissionDenied("You do not have permission to view analytics.")


def require_resource_search_view(
    *,
    token: str,
    resource_type: str,
    institution_id: str | None = None,
) -> None:
    permission = SEARCH_PERMISSION_BY_RESOURCE[resource_type]
    scope_type = "institution" if institution_id else "platform"
    if not remote_authorization_check(
        token=token,
        permission=permission,
        scope_type=scope_type,
        scope_id=institution_id,
    ):
        raise PermissionDenied("You do not have permission to search this resource type.")


def allowed_search_resource_types(*, token: str, institution_id: str | None = None) -> list[str]:
    scope_type = "institution" if institution_id else "platform"
    allowed = []
    for resource_type, permission in SEARCH_PERMISSION_BY_RESOURCE.items():
        if remote_authorization_check(
            token=token,
            permission=permission,
            scope_type=scope_type,
            scope_id=institution_id,
        ):
            allowed.append(str(resource_type))
    if not allowed:
        raise PermissionDenied("You do not have permission to search analytics records.")
    return allowed


def require_profile_view(*, token: str, institution_id: str | None) -> None:
    scope_type = "institution" if institution_id else "platform"
    if not remote_authorization_check(
        token=token,
        permission="profile.view",
        scope_type=scope_type,
        scope_id=institution_id,
    ):
        raise PermissionDenied("You do not have permission to view this profile dashboard.")


def require_student_profile(profile: dict[str, Any]) -> None:
    if profile.get("profile_type") != "student":
        raise PermissionDenied("Student dashboard requires a student profile.")


def require_instructor_profile(profile: dict[str, Any]) -> None:
    if profile.get("profile_type") != "instructor":
        raise PermissionDenied("Instructor dashboard requires an instructor profile.")


def cached_dashboard_payload(
    *,
    portal: str,
    scope_type: str,
    scope_id,
    profile: dict | None = None,
    institution_id=None,
) -> dict[str, Any]:
    cache_key = _dashboard_cache_key(
        portal=portal,
        scope_type=scope_type,
        scope_id=scope_id,
        profile_id=profile.get("id") if profile else None,
    )
    cached = get_json_cache(_redis_client(), cache_key)
    if cached is not None:
        return cached

    payload = dashboard_payload(
        portal=portal,
        scope_type=scope_type,
        scope_id=scope_id,
        profile=profile,
        institution_id=institution_id,
    )
    set_json_cache(
        _redis_client(),
        cache_key,
        payload,
        settings.ANALYTICS_DASHBOARD_CACHE_TTL_SECONDS,
    )
    return payload


def cached_platform_dashboard_payload(profile: dict | None = None) -> dict[str, Any]:
    return cached_dashboard_payload(
        portal="admin",
        scope_type=DashboardScopeType.PLATFORM,
        scope_id=PLATFORM_SCOPE_ID,
        profile=profile,
    )


def invalidate_dashboard_cache(*, scope_type: str, scope_id=None) -> None:
    suffix = [scope_type]
    if scope_id is not None:
        suffix.append(str(scope_id))
    try:
        client = _redis_client()
        for key in client.scan_iter(f"{_key_builder().prefix_for('cache', 'dashboard', suffix)}*"):
            client.delete(key)
    except (redis.RedisError, OSError):
        return


@transaction.atomic
def ingest_event(
    validated_data: dict[str, Any],
    *,
    publish_ingested_event: bool = True,
) -> tuple[EventFact, bool]:
    event, created = EventFact.objects.get_or_create(
        event_id=validated_data["event_id"],
        defaults={
            "event_type": validated_data["event_type"],
            "producer_service": validated_data["producer_service"],
            "aggregate_id": validated_data["aggregate_id"],
            "institution_id": validated_data.get("institution_id"),
            "occurred_at": validated_data["occurred_at"],
            "payload": validated_data.get("payload", {}),
        },
    )
    if created and publish_ingested_event:
        publish_analytics_event(
            event_type="AnalyticsEventIngested",
            aggregate_id=event.id,
            payload={
                "source_event_id": str(event.event_id),
                "source_event_type": event.event_type,
                "producer_service": event.producer_service,
                "institution_id": str(event.institution_id) if event.institution_id else None,
            },
        )
    return event, created


def handle_kafka_analytics_event(event: dict[str, Any]) -> dict[str, Any]:
    stored_event, created = ingest_event(
        {
            "event_id": event["event_id"],
            "event_type": event["event_type"],
            "producer_service": event["producer_service"],
            "aggregate_id": event["aggregate_id"],
            "institution_id": event["payload"].get("institution_id"),
            "occurred_at": event["timestamp"],
            "payload": event["payload"],
        },
        publish_ingested_event=False,
    )
    if not created:
        raise DuplicateEvent()
    return {"status": "processed", "event_id": str(stored_event.event_id)}


def publish_analytics_event(
    *,
    event_type: str,
    aggregate_id,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return publish_kafka_event(
        event_type=event_type,
        aggregate_id=aggregate_id,
        producer_service=settings.SERVICE_NAME,
        payload=payload,
    )


def _redis_client():
    return redis_client(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT_SECONDS,
    )


def _key_builder() -> RedisKeyBuilder:
    return RedisKeyBuilder(service=settings.SERVICE_NAME, env=settings.REDIS_ENV)


def _dashboard_cache_key(*, portal: str, scope_type: str, scope_id, profile_id=None) -> str:
    return _key_builder().key(
        "cache",
        "dashboard",
        [scope_type, str(scope_id), portal, str(profile_id or "none")],
    )


def create_report_snapshot(
    *,
    validated_data: dict[str, Any],
    generated_by_profile_id,
) -> ReportSnapshot:
    return ReportSnapshot.objects.create(
        institution_id=validated_data.get("institution_id"),
        report_type=validated_data["report_type"],
        parameters=validated_data.get("parameters", {}),
        result_payload=validated_data.get("result_payload", {}),
        generated_by_profile_id=generated_by_profile_id,
    )


@transaction.atomic
def upsert_search_index_record(validated_data: dict[str, Any]) -> tuple[SearchIndexRecord, bool]:
    record, created = SearchIndexRecord.objects.update_or_create(
        resource_type=validated_data["resource_type"],
        resource_id=validated_data["resource_id"],
        defaults={
            "institution_id": validated_data.get("institution_id"),
            "search_text": validated_data["search_text"],
            "metadata": validated_data.get("metadata", {}),
            "updated_at": timezone.now(),
        },
    )
    return record, created


@transaction.atomic
def delete_search_index_record(*, resource_type: str, resource_id: str) -> bool:
    deleted_count, _ = SearchIndexRecord.objects.filter(
        resource_type=resource_type,
        resource_id=resource_id,
    ).delete()
    return deleted_count > 0


@transaction.atomic
def upsert_dashboard_aggregate(validated_data: dict[str, Any]) -> tuple[DashboardAggregate, bool]:
    aggregate, created = DashboardAggregate.objects.update_or_create(
        scope_type=validated_data["scope_type"],
        scope_id=validated_data["scope_id"],
        metric_date=validated_data["metric_date"],
        defaults={
            "metrics": validated_data.get("metrics", {}),
            "computed_at": timezone.now(),
        },
    )
    invalidate_dashboard_cache(scope_type=aggregate.scope_type, scope_id=aggregate.scope_id)
    return aggregate, created


def create_usage_metric(validated_data: dict[str, Any]) -> UsageMetric:
    return UsageMetric.objects.create(**validated_data)


def generate_report_snapshot(
    *,
    validated_data: dict[str, Any],
    generated_by_profile_id,
) -> ReportSnapshot:
    payload = build_report_payload(
        report_type=validated_data["report_type"],
        institution_id=validated_data.get("institution_id"),
        parameters=validated_data.get("parameters", {}),
    )
    snapshot = ReportSnapshot.objects.create(
        institution_id=validated_data.get("institution_id"),
        report_type=validated_data["report_type"],
        parameters=validated_data.get("parameters", {}),
        result_payload=payload,
        generated_by_profile_id=generated_by_profile_id,
    )
    publish_analytics_event(
        event_type="AnalyticsReportGenerated",
        aggregate_id=snapshot.id,
        payload={
            "institution_id": str(snapshot.institution_id) if snapshot.institution_id else None,
            "report_type": snapshot.report_type,
            "generated_by_profile_id": str(snapshot.generated_by_profile_id)
            if snapshot.generated_by_profile_id
            else None,
        },
    )
    return snapshot


def build_report_payload(
    *,
    report_type: str,
    institution_id,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    if report_type == ReportType.ACTIVE_USERS:
        return _active_users_report(institution_id=institution_id, parameters=parameters)
    if report_type == ReportType.ENROLLMENTS:
        return _enrollments_report(institution_id=institution_id, parameters=parameters)
    if report_type == ReportType.COMPLETION_RATES:
        return _completion_rates_report(institution_id=institution_id, parameters=parameters)
    if report_type == ReportType.ASSESSMENT_RESULTS:
        return _assessment_results_report(institution_id=institution_id, parameters=parameters)
    if report_type == ReportType.SYSTEM_USAGE:
        return _system_usage_report(institution_id=institution_id, parameters=parameters)
    raise APIException("Unsupported report type.")


def _search_records_for_report(*, resource_type: str, institution_id) -> Any:
    queryset = SearchIndexRecord.objects.filter(resource_type=resource_type)
    if institution_id:
        queryset = queryset.filter(institution_id=institution_id)
    return queryset


def _events_for_report(*, institution_id, parameters: dict[str, Any]) -> Any:
    queryset = EventFact.objects.all()
    if institution_id:
        queryset = queryset.filter(institution_id=institution_id)
    if start_at := _parse_parameter_datetime(parameters.get("start_at")):
        queryset = queryset.filter(occurred_at__gte=start_at)
    if end_at := _parse_parameter_datetime(parameters.get("end_at")):
        queryset = queryset.filter(occurred_at__lte=end_at)
    return queryset


def _usage_metrics_for_report(*, institution_id, parameters: dict[str, Any]) -> Any:
    queryset = UsageMetric.objects.all()
    if institution_id:
        queryset = queryset.filter(
            scope_type=DashboardScopeType.INSTITUTION,
            scope_id=institution_id,
        )
    if start_at := _parse_parameter_datetime(parameters.get("start_at")):
        queryset = queryset.filter(bucket_start_at__gte=start_at)
    if end_at := _parse_parameter_datetime(parameters.get("end_at")):
        queryset = queryset.filter(bucket_end_at__lte=end_at)
    return queryset


def _parse_parameter_datetime(value) -> Any:
    if not value or not isinstance(value, str):
        return None
    parsed = parse_datetime(value)
    if parsed and timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone=dt_timezone.utc)
    return parsed


def _metadata_counts(records, *, key: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for metadata in records.values_list("metadata", flat=True):
        value = (metadata or {}).get(key) or "unknown"
        counter[str(value)] += 1
    return dict(sorted(counter.items()))


def _decimal_to_float(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _active_users_report(*, institution_id, parameters: dict[str, Any]) -> dict[str, Any]:
    users = _search_records_for_report(
        resource_type=SearchResourceType.USER,
        institution_id=institution_id,
    )
    active_users = users.filter(metadata__status="active")
    events = _events_for_report(institution_id=institution_id, parameters=parameters)
    return {
        "report_type": ReportType.ACTIVE_USERS,
        "summary": {
            "active_user_count": active_users.count(),
            "indexed_user_count": users.count(),
            "activity_event_count": events.count(),
        },
        "users_by_status": _metadata_counts(users, key="status"),
    }


def _enrollments_report(*, institution_id, parameters: dict[str, Any]) -> dict[str, Any]:
    enrollments = _search_records_for_report(
        resource_type=SearchResourceType.ENROLLMENT,
        institution_id=institution_id,
    )
    events = _events_for_report(institution_id=institution_id, parameters=parameters).filter(
        event_type__icontains="Enrollment",
    )
    return {
        "report_type": ReportType.ENROLLMENTS,
        "summary": {
            "indexed_enrollment_count": enrollments.count(),
            "enrollment_event_count": events.count(),
        },
        "enrollments_by_status": _metadata_counts(enrollments, key="status"),
    }


def _completion_rates_report(*, institution_id, parameters: dict[str, Any]) -> dict[str, Any]:
    metrics = _usage_metrics_for_report(
        institution_id=institution_id,
        parameters=parameters,
    ).filter(metric_name="course_completion_percent")
    events = _events_for_report(institution_id=institution_id, parameters=parameters).filter(
        event_type="CourseCompleted",
    )
    average = metrics.aggregate(value=Avg("metric_value"))["value"]
    return {
        "report_type": ReportType.COMPLETION_RATES,
        "summary": {
            "metric_count": metrics.count(),
            "average_completion_percent": _decimal_to_float(average),
            "course_completed_event_count": events.count(),
        },
    }


def _assessment_results_report(*, institution_id, parameters: dict[str, Any]) -> dict[str, Any]:
    metrics = _usage_metrics_for_report(
        institution_id=institution_id,
        parameters=parameters,
    ).filter(metric_name="assessment_score_percent")
    submissions = _search_records_for_report(
        resource_type=SearchResourceType.SUBMISSION,
        institution_id=institution_id,
    )
    average = metrics.aggregate(value=Avg("metric_value"))["value"]
    return {
        "report_type": ReportType.ASSESSMENT_RESULTS,
        "summary": {
            "metric_count": metrics.count(),
            "average_score_percent": _decimal_to_float(average),
            "indexed_submission_count": submissions.count(),
        },
        "submissions_by_status": _metadata_counts(submissions, key="submission_status"),
    }


def _system_usage_report(*, institution_id, parameters: dict[str, Any]) -> dict[str, Any]:
    metrics = _usage_metrics_for_report(institution_id=institution_id, parameters=parameters)
    events = _events_for_report(institution_id=institution_id, parameters=parameters)
    metric_names: Counter[str] = Counter()
    for metric_name in metrics.values_list("metric_name", flat=True):
        metric_names[str(metric_name)] += 1
    event_types: Counter[str] = Counter()
    for event_type in events.values_list("event_type", flat=True):
        event_types[str(event_type)] += 1
    return {
        "report_type": ReportType.SYSTEM_USAGE,
        "summary": {
            "usage_metric_count": metrics.count(),
            "event_count": events.count(),
        },
        "metrics_by_name": dict(sorted(metric_names.items())),
        "events_by_type": dict(sorted(event_types.items())),
    }


def dashboard_scope_for_profile(profile: dict[str, Any]) -> tuple[str, str]:
    profile_type = profile.get("profile_type")
    if profile_type == "student":
        return DashboardScopeType.STUDENT, profile["id"]
    if profile_type == "instructor":
        return DashboardScopeType.INSTRUCTOR, profile["id"]
    raise PermissionDenied("Profile type does not have an analytics dashboard.")


def platform_scope() -> tuple[str, str]:
    return DashboardScopeType.PLATFORM, str(PLATFORM_SCOPE_ID)
