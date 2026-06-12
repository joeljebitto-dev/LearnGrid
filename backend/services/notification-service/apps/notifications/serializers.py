from __future__ import annotations

from rest_framework import serializers

from .models import (
    DeliveryAttempt,
    DeliveryStatus,
    Notification,
    NotificationChannel,
    NotificationTemplate,
    TemplateStatus,
    UserNotificationPreference,
)


SUPPORTED_EVENT_TYPES = [
    "StudentEnrolled",
    "AssignmentDueSoon",
    "GradePublished",
    "CourseCompleted",
]
NOTIFICATION_SORT_CHOICES = ["created_at", "-created_at", "read_at", "-read_at"]


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = [
            "id",
            "event_type",
            "channel",
            "subject_template",
            "body_template",
            "status",
            "created_at",
            "updated_at",
        ]


class NotificationTemplateCreateSerializer(serializers.Serializer):
    event_type = serializers.CharField(max_length=80)
    channel = serializers.ChoiceField(
        choices=NotificationChannel.choices, default=NotificationChannel.IN_APP
    )
    subject_template = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    body_template = serializers.CharField()
    status = serializers.ChoiceField(choices=TemplateStatus.choices, default=TemplateStatus.ACTIVE)


class NotificationTemplateUpdateSerializer(serializers.Serializer):
    subject_template = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    body_template = serializers.CharField(required=False)
    status = serializers.ChoiceField(choices=TemplateStatus.choices, required=False)


class NotificationTemplateSearchSerializer(serializers.Serializer):
    event_type = serializers.CharField(required=False, max_length=80)
    channel = serializers.ChoiceField(choices=NotificationChannel.choices, required=False)
    status = serializers.ChoiceField(choices=TemplateStatus.choices, required=False)


class DeliveryAttemptSerializer(serializers.ModelSerializer):
    notification_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = DeliveryAttempt
        fields = [
            "id",
            "notification_id",
            "channel",
            "status",
            "provider_message_id",
            "error_message",
            "attempted_at",
        ]


class NotificationSerializer(serializers.ModelSerializer):
    delivery_attempts = DeliveryAttemptSerializer(many=True, read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient_profile_id",
            "event_type",
            "title",
            "body",
            "payload",
            "read_at",
            "created_at",
            "deleted_at",
            "delivery_attempts",
        ]


class NotificationSearchSerializer(serializers.Serializer):
    recipient_profile_id = serializers.UUIDField(required=False)
    event_type = serializers.CharField(required=False, max_length=80)
    unread = serializers.BooleanField(required=False)
    include_deleted = serializers.BooleanField(required=False, default=False)
    sort = serializers.ChoiceField(
        choices=NOTIFICATION_SORT_CHOICES, default="-created_at", required=False
    )

    def validate(self, attrs):
        if "unread" not in self.initial_data:
            attrs.pop("unread", None)
        return attrs


class NotificationEventIngestSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()
    event_type = serializers.ChoiceField(choices=SUPPORTED_EVENT_TYPES)
    aggregate_id = serializers.UUIDField()
    producer_service = serializers.CharField(required=False, allow_blank=True, max_length=80)
    timestamp = serializers.DateTimeField(required=False)
    payload = serializers.JSONField()


class UserNotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationPreference
        fields = [
            "id",
            "profile_id",
            "event_type",
            "channel",
            "enabled",
            "created_at",
            "updated_at",
        ]


class UserNotificationPreferenceUpsertSerializer(serializers.Serializer):
    profile_id = serializers.UUIDField(required=False)
    event_type = serializers.CharField(max_length=80)
    channel = serializers.ChoiceField(choices=NotificationChannel.choices)
    enabled = serializers.BooleanField(default=True)


class UserNotificationPreferenceSearchSerializer(serializers.Serializer):
    profile_id = serializers.UUIDField(required=False)
    event_type = serializers.CharField(required=False, max_length=80)
    channel = serializers.ChoiceField(choices=NotificationChannel.choices, required=False)


class DeliveryAttemptSearchSerializer(serializers.Serializer):
    notification_id = serializers.UUIDField(required=False)
    channel = serializers.ChoiceField(choices=NotificationChannel.choices, required=False)
    status = serializers.ChoiceField(choices=DeliveryStatus.choices, required=False)
