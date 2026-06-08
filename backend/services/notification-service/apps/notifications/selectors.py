from __future__ import annotations

from .models import DeliveryAttempt, Notification, NotificationTemplate, UserNotificationPreference


def notification_template_queryset():
    return NotificationTemplate.objects.all()


def notification_queryset():
    return Notification.objects.prefetch_related("delivery_attempts")


def delivery_attempt_queryset():
    return DeliveryAttempt.objects.select_related("notification")


def user_notification_preference_queryset():
    return UserNotificationPreference.objects.all()


def search_notification_templates(filters: dict):
    queryset = notification_template_queryset()
    for field in ["event_type", "channel", "status"]:
        if value := filters.get(field):
            queryset = queryset.filter(**{field: value})
    return queryset.order_by("event_type", "channel", "id")


def search_notifications(filters: dict):
    queryset = notification_queryset()
    if not filters.get("include_deleted"):
        queryset = queryset.filter(deleted_at__isnull=True)
    for field in ["recipient_profile_id", "event_type"]:
        if value := filters.get(field):
            queryset = queryset.filter(**{field: value})
    if "unread" in filters:
        queryset = queryset.filter(read_at__isnull=filters["unread"])
    return queryset.order_by(filters.get("sort") or "-created_at", "id")


def search_delivery_attempts(filters: dict):
    queryset = delivery_attempt_queryset()
    for field in ["notification_id", "channel", "status"]:
        if value := filters.get(field):
            queryset = queryset.filter(**{field: value})
    return queryset.order_by("-attempted_at", "id")


def search_user_notification_preferences(filters: dict):
    queryset = user_notification_preference_queryset()
    for field in ["profile_id", "event_type", "channel"]:
        if value := filters.get(field):
            queryset = queryset.filter(**{field: value})
    return queryset.order_by("event_type", "channel", "id")
