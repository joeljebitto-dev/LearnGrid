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
    decimal_value,
    load_manifest,
    now,
    planned,
    profile_id,
    uuid_value,
)

from apps.progress.models import (  # noqa: E402
    AssessmentProgress,
    AssessmentProgressStatus,
    CourseProgress,
    CourseProgressStatus,
    LessonProgress,
    LessonProgressStatus,
    ProgressEvent,
    VideoProgress,
)


class Command(BaseCommand):
    help = "Seed LearnGrid demo sample data for progress-service."

    def add_arguments(self, parser) -> None:
        add_seed_arguments(parser, __file__)

    def handle(self, *args, **options) -> None:
        manifest = load_manifest(options["manifest"])
        records = [
            "lesson_progress",
            "video_progress",
            "assessment_progress",
            "course_progress",
            "progress_events",
        ]
        if options["dry_run"]:
            planned(self, "progress-service", manifest, records)
            return
        with transaction.atomic():
            if options["reset_sample_data"]:
                self.reset(manifest)
            self.seed(manifest)
        self.stdout.write(self.style.SUCCESS("Seeded progress-service sample data."))

    def reset(self, manifest: dict) -> None:
        data = manifest["progress"]
        LessonProgress.objects.filter(id=uuid_value(data["lesson_progress_id"])).delete()
        VideoProgress.objects.filter(id=uuid_value(data["video_progress_id"])).delete()
        AssessmentProgress.objects.filter(id=uuid_value(data["assessment_progress_id"])).delete()
        CourseProgress.objects.filter(id=uuid_value(data["course_progress_id"])).delete()
        ProgressEvent.objects.filter(event_id=uuid_value(data["event_id"])).delete()

    def seed(self, manifest: dict) -> None:
        data = manifest["progress"]
        completed_at = now()
        LessonProgress.objects.update_or_create(
            id=uuid_value(data["lesson_progress_id"]),
            defaults={
                "student_profile_id": profile_id(manifest, "student"),
                "course_id": course_id(manifest),
                "lesson_id": uuid_value(manifest["courses"]["main"]["lesson_id"]),
                "status": LessonProgressStatus.COMPLETED,
                "view_count": 3,
                "first_viewed_at": completed_at,
                "completed_at": completed_at,
            },
        )
        VideoProgress.objects.update_or_create(
            id=uuid_value(data["video_progress_id"]),
            defaults={
                "student_profile_id": profile_id(manifest, "student"),
                "content_asset_id": uuid_value(manifest["content"]["lesson_video"]["id"]),
                "course_id": course_id(manifest),
                "last_position_seconds": 600,
                "duration_seconds": 600,
                "percent_complete": decimal_value("100.00"),
                "completed_at": completed_at,
            },
        )
        AssessmentProgress.objects.update_or_create(
            id=uuid_value(data["assessment_progress_id"]),
            defaults={
                "student_profile_id": profile_id(manifest, "student"),
                "assessment_id": uuid_value(manifest["assessment"]["quiz_assessment_id"]),
                "course_id": course_id(manifest),
                "status": AssessmentProgressStatus.GRADED,
                "attempt_count": 1,
                "last_submitted_at": completed_at,
            },
        )
        CourseProgress.objects.update_or_create(
            id=uuid_value(data["course_progress_id"]),
            defaults={
                "student_profile_id": profile_id(manifest, "student"),
                "course_id": course_id(manifest),
                "completion_percent": decimal_value("100.00"),
                "lessons_completed": 1,
                "assessments_completed": 1,
                "status": CourseProgressStatus.COMPLETED,
                "completed_at": completed_at,
            },
        )
        ProgressEvent.objects.update_or_create(
            event_id=uuid_value(data["event_id"]),
            defaults={
                "id": uuid_value(data["event_id"]),
                "event_type": "CourseCompleted",
                "aggregate_id": course_id(manifest),
                "payload": {
                    "seed_namespace": manifest["seed_namespace"],
                    "student_profile_id": str(profile_id(manifest, "student")),
                    "completion_percent": 100,
                },
            },
        )
