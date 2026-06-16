from __future__ import annotations

import sys
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

ROOT = Path(__file__).resolve().parents[7]
sys.path.append(str(ROOT / "scripts" / "sample_data"))

from seed_helpers import (  # noqa: E402
    add_seed_arguments,
    course_id,
    load_manifest,
    planned,
    profile_id,
    uuid_value,
)

from apps.notifications.models import (  # noqa: E402
    DeliveryAttempt,
    DeliveryStatus,
    Notification,
    NotificationChannel,
    NotificationTemplate,
    TemplateStatus,
    UserNotificationPreference,
)


class Command(BaseCommand):
    help = "Seed LearnGrid demo sample data for notification-service."

    def add_arguments(self, parser) -> None:
        add_seed_arguments(parser, __file__)

    def handle(self, *args, **options) -> None:
        manifest = load_manifest(options["manifest"])
        records = ["notification_templates", "preferences", "notifications", "delivery_attempts"]
        if options["dry_run"]:
            planned(self, "notification-service", manifest, records)
            return
        with transaction.atomic():
            if options["reset_sample_data"]:
                self.reset(manifest)
            self.seed(manifest)
        self.stdout.write(self.style.SUCCESS("Seeded notification-service sample data."))

    def reset(self, manifest: dict) -> None:
        data = manifest["notification"]
        DeliveryAttempt.objects.filter(id=uuid_value(data["delivery_attempt_id"])).delete()
        Notification.objects.filter(id=uuid_value(data["notification_id"])).delete()
        UserNotificationPreference.objects.filter(id=uuid_value(data["preference_id"])).delete()
        NotificationTemplate.objects.filter(id=uuid_value(data["template_id"])).delete()

    def seed(self, manifest: dict) -> None:
        data = manifest["notification"]
        template, _created = NotificationTemplate.objects.update_or_create(
            id=uuid_value(data["template_id"]),
            defaults={
                "event_type": "GradePublished",
                "channel": NotificationChannel.IN_APP,
                "subject_template": "Grade published",
                "body_template": "Your demo course grade is available.",
                "status": TemplateStatus.ACTIVE,
            },
        )
        UserNotificationPreference.objects.update_or_create(
            id=uuid_value(data["preference_id"]),
            defaults={
                "profile_id": profile_id(manifest, "student"),
                "event_type": template.event_type,
                "channel": NotificationChannel.IN_APP,
                "enabled": True,
            },
        )
        notification, _created = Notification.objects.update_or_create(
            id=uuid_value(data["notification_id"]),
            defaults={
                "recipient_profile_id": profile_id(manifest, "student"),
                "event_type": template.event_type,
                "title": "Your demo grade is ready",
                "body": "You scored 90% in Foundations of Web Learning.",
                "payload": {
                    "seed_namespace": manifest["seed_namespace"],
                    "course_id": str(course_id(manifest)),
                    "grade_record_id": manifest["grading"]["quiz_grade_id"],
                },
                "read_at": None,
                "deleted_at": None,
            },
        )
        DeliveryAttempt.objects.update_or_create(
            id=uuid_value(data["delivery_attempt_id"]),
            defaults={
                "notification": notification,
                "channel": NotificationChannel.IN_APP,
                "status": DeliveryStatus.SENT,
                "provider_message_id": "learngrid-demo-notification",
                "error_message": None,
            },
        )
