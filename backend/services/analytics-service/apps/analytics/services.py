from __future__ import annotations

import json
from typing import Any
from urllib import error, request as urlrequest

from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import APIException, NotFound, PermissionDenied

from .models import DashboardScopeType, EventFact, ReportSnapshot
from .permissions import remote_authorization_check
from .selectors import PLATFORM_SCOPE_ID


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


@transaction.atomic
def ingest_event(validated_data: dict[str, Any]) -> tuple[EventFact, bool]:
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
    return event, created


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


def dashboard_scope_for_profile(profile: dict[str, Any]) -> tuple[str, str]:
    profile_type = profile.get("profile_type")
    if profile_type == "student":
        return DashboardScopeType.STUDENT, profile["id"]
    if profile_type == "instructor":
        return DashboardScopeType.INSTRUCTOR, profile["id"]
    raise PermissionDenied("Profile type does not have an analytics dashboard.")


def platform_scope() -> tuple[str, str]:
    return DashboardScopeType.PLATFORM, str(PLATFORM_SCOPE_ID)
