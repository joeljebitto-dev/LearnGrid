from __future__ import annotations

import json
from collections import defaultdict
from string import Formatter
from typing import Any
from urllib import error, parse, request as urlrequest

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from learngrid_events import DuplicateEvent
from learngrid_events import publish_event as publish_kafka_event
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError

from .models import (
    DeliveryAttempt,
    DeliveryStatus,
    Notification,
    NotificationChannel,
    NotificationTemplate,
    TemplateStatus,
    UserNotificationPreference,
)


DEFAULT_TEMPLATES = {
    "StudentEnrolled": {
        "subject": "Enrollment confirmed",
        "body": "You have been enrolled in {course_title}.",
    },
    "AssignmentDueSoon": {
        "subject": "Assignment due soon",
        "body": "{assignment_title} is due {due_at}.",
    },
    "GradePublished": {
        "subject": "Grade published",
        "body": "Your grade for {assessment_title} is now available.",
    },
    "CourseCompleted": {
        "subject": "Course completed",
        "body": "You completed {course_title}.",
    },
}


class UserServiceError(APIException):
    status_code = 502
    default_code = "user_service_error"
    default_detail = "User-service request failed."


def auth_token(request) -> str:
    return str(request.auth)


def _json_request(
    *,
    base_url: str,
    path: str,
    token: str,
    query: dict[str, Any] | None = None,
    error_class: type[APIException] = APIException,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}{path}"
    if query:
        url = f"{url}?{parse.urlencode({key: str(value) for key, value in query.items() if value is not None})}"
    request = urlrequest.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="GET",
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


def create_notification_template(*, validated_data: dict[str, Any]) -> NotificationTemplate:
    template, _created = NotificationTemplate.objects.update_or_create(
        event_type=validated_data["event_type"],
        channel=validated_data["channel"],
        defaults={
            "subject_template": validated_data.get("subject_template"),
            "body_template": validated_data["body_template"],
            "status": validated_data["status"],
        },
    )
    return template


def update_notification_template(
    *,
    template: NotificationTemplate,
    validated_data: dict[str, Any],
) -> NotificationTemplate:
    for field in ["subject_template", "body_template", "status"]:
        if field in validated_data:
            setattr(template, field, validated_data[field])
    template.save()
    return template


def upsert_user_notification_preference(*, validated_data: dict[str, Any]) -> UserNotificationPreference:
    preference, _created = UserNotificationPreference.objects.update_or_create(
        profile_id=validated_data["profile_id"],
        event_type=validated_data["event_type"],
        channel=validated_data["channel"],
        defaults={"enabled": validated_data["enabled"]},
    )
    return preference


@transaction.atomic
def ingest_notification_event(*, event: dict[str, Any]) -> dict[str, Any]:
    recipients = recipient_profile_ids_for_event(event_type=event["event_type"], payload=event["payload"])
    notifications = []
    duplicate_count = 0
    skipped_count = 0

    for recipient_profile_id in recipients:
        existing = find_existing_notification(
            recipient_profile_id=recipient_profile_id,
            event_type=event["event_type"],
            event_id=event["event_id"],
        )
        if existing:
            notifications.append(existing)
            duplicate_count += 1
            continue
        if not preference_enabled(
            profile_id=recipient_profile_id,
            event_type=event["event_type"],
            channel=NotificationChannel.IN_APP,
        ):
            skipped_count += 1
            continue

        template = active_template_for_event(event["event_type"])
        title = render_template(template.subject_template or template.event_type, event["payload"])
        body = render_template(template.body_template, event["payload"])
        notification = Notification.objects.create(
            recipient_profile_id=recipient_profile_id,
            event_type=event["event_type"],
            title=title[:255],
            body=body,
            payload={
                **event["payload"],
                "source_event_id": str(event["event_id"]),
                "aggregate_id": str(event["aggregate_id"]),
                "producer_service": event.get("producer_service"),
            },
        )
        create_delivery_attempt(notification=notification, payload=event["payload"])
        notifications.append(notification)

    if duplicate_count and duplicate_count == len(recipients):
        status = "duplicate"
    elif notifications:
        status = "processed"
    else:
        status = "skipped"
    return {
        "status": status,
        "notifications": notifications,
        "skipped_count": skipped_count,
        "duplicate_count": duplicate_count,
    }


def handle_kafka_notification_event(event: dict[str, Any]) -> dict[str, Any]:
    if event["event_type"] not in DEFAULT_TEMPLATES:
        return {"status": "skipped", "event_id": event["event_id"]}
    result = ingest_notification_event(event=event)
    if result["status"] == "duplicate":
        raise DuplicateEvent()
    publish_notification_event(
        event_type="NotificationEventProcessed",
        aggregate_id=event["aggregate_id"],
        payload={
            "source_event_id": event["event_id"],
            "source_event_type": event["event_type"],
            "status": result["status"],
            "notification_count": len(result["notifications"]),
            "skipped_count": result["skipped_count"],
        },
    )
    return result


def recipient_profile_ids_for_event(*, event_type: str, payload: dict[str, Any]) -> list[str]:
    if recipients := payload.get("recipient_profile_ids"):
        if not isinstance(recipients, list) or not recipients:
            raise ValidationError({"recipient_profile_ids": "Must be a non-empty list."})
        return [str(recipient) for recipient in recipients]

    field_by_event = {
        "StudentEnrolled": "student_profile_id",
        "AssignmentDueSoon": "student_profile_id",
        "GradePublished": "student_profile_id",
        "CourseCompleted": "student_profile_id",
    }
    field = field_by_event.get(event_type)
    if not field or not payload.get(field):
        raise ValidationError({"payload": f"{event_type} requires {field}."})
    return [str(payload[field])]


def find_existing_notification(*, recipient_profile_id, event_type: str, event_id) -> Notification | None:
    return (
        Notification.objects.filter(
            recipient_profile_id=recipient_profile_id,
            event_type=event_type,
            payload__source_event_id=str(event_id),
            deleted_at__isnull=True,
        )
        .order_by("id")
        .first()
    )


def preference_enabled(*, profile_id, event_type: str, channel: str) -> bool:
    preference = UserNotificationPreference.objects.filter(
        profile_id=profile_id,
        event_type=event_type,
        channel=channel,
    ).first()
    return preference.enabled if preference else True


def active_template_for_event(event_type: str) -> NotificationTemplate:
    template = NotificationTemplate.objects.filter(
        event_type=event_type,
        channel=NotificationChannel.IN_APP,
        status=TemplateStatus.ACTIVE,
    ).first()
    if template:
        return template
    defaults = DEFAULT_TEMPLATES[event_type]
    template, _created = NotificationTemplate.objects.update_or_create(
        event_type=event_type,
        channel=NotificationChannel.IN_APP,
        defaults={
            "subject_template": defaults["subject"],
            "body_template": defaults["body"],
            "status": TemplateStatus.ACTIVE,
        },
    )
    return template


def render_template(template: str, payload: dict[str, Any]) -> str:
    safe_payload = defaultdict(str, {key: "" if value is None else str(value) for key, value in payload.items()})
    return Formatter().vformat(template, (), safe_payload)


def create_delivery_attempt(*, notification: Notification, payload: dict[str, Any]) -> DeliveryAttempt:
    if payload.get("force_delivery_failure") is True:
        return DeliveryAttempt.objects.create(
            notification=notification,
            channel=NotificationChannel.IN_APP,
            status=DeliveryStatus.FAILED,
            error_message=str(payload.get("delivery_error_message") or "Forced delivery failure."),
        )
    return DeliveryAttempt.objects.create(
        notification=notification,
        channel=NotificationChannel.IN_APP,
        status=DeliveryStatus.SENT,
        provider_message_id=f"in-app:{notification.id}",
    )


def publish_notification_event(*, event_type: str, aggregate_id, payload: dict[str, Any]) -> dict[str, Any]:
    return publish_kafka_event(
        event_type=event_type,
        aggregate_id=aggregate_id,
        producer_service=settings.SERVICE_NAME,
        payload=payload,
    )


def mark_notification_read(*, notification: Notification) -> Notification:
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
    return notification


def mark_notification_unread(*, notification: Notification) -> Notification:
    if notification.read_at is not None:
        notification.read_at = None
        notification.save(update_fields=["read_at"])
    return notification


def mark_all_notifications_read(*, recipient_profile_id) -> int:
    return Notification.objects.filter(
        recipient_profile_id=recipient_profile_id,
        read_at__isnull=True,
        deleted_at__isnull=True,
    ).update(read_at=timezone.now())
