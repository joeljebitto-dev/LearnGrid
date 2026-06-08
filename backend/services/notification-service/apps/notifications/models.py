from __future__ import annotations

import uuid

from django.db import models


class NotificationChannel(models.TextChoices):
    IN_APP = "in_app", "In app"
    EMAIL = "email", "Email"
    SMS = "sms", "SMS"
    PUSH = "push", "Push"


class TemplateStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class DeliveryStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class NotificationTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=80)
    channel = models.CharField(
        max_length=32,
        choices=NotificationChannel.choices,
        default=NotificationChannel.IN_APP,
    )
    subject_template = models.TextField(null=True, blank=True)
    body_template = models.TextField()
    status = models.CharField(
        max_length=24,
        choices=TemplateStatus.choices,
        default=TemplateStatus.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_templates"
        constraints = [
            models.UniqueConstraint(
                fields=["event_type", "channel"],
                name="uq_notify_tpl_event_channel",
            ),
        ]
        indexes = [
            models.Index(fields=["status"], name="idx_notify_tpl_status"),
        ]


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient_profile_id = models.UUIDField()
    event_type = models.CharField(max_length=80)
    title = models.CharField(max_length=255)
    body = models.TextField()
    payload = models.JSONField(default=dict)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications"
        indexes = [
            models.Index(fields=["recipient_profile_id", "-created_at"], name="idx_notify_recipient_created"),
            models.Index(fields=["recipient_profile_id", "read_at"], name="idx_notify_recipient_unread"),
            models.Index(fields=["event_type"], name="idx_notifications_event_type"),
        ]


class DeliveryAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="delivery_attempts",
    )
    channel = models.CharField(max_length=32, choices=NotificationChannel.choices)
    status = models.CharField(
        max_length=24,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.QUEUED,
    )
    provider_message_id = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "delivery_attempts"
        indexes = [
            models.Index(fields=["notification"], name="idx_delivery_notification"),
            models.Index(fields=["channel", "status"], name="idx_delivery_channel_status"),
        ]


class UserNotificationPreference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile_id = models.UUIDField()
    event_type = models.CharField(max_length=80)
    channel = models.CharField(max_length=32, choices=NotificationChannel.choices)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_notification_preferences"
        constraints = [
            models.UniqueConstraint(
                fields=["profile_id", "event_type", "channel"],
                name="uq_notify_pref_profile_event",
            ),
        ]
        indexes = [
            models.Index(fields=["profile_id"], name="idx_notify_pref_profile"),
        ]
