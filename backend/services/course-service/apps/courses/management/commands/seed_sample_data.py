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
    institution_id,
    load_manifest,
    now,
    planned,
    profile_id,
    uuid_value,
)

from apps.courses.models import (  # noqa: E402
    Course,
    CourseCategory,
    CourseCategoryLink,
    CourseDifficulty,
    CourseModule,
    CoursePrerequisite,
    CourseRevision,
    CourseStatus,
    CourseTag,
    CourseTagLink,
    LearningOutcome,
    Lesson,
    StructureStatus,
    Topic,
)


class Command(BaseCommand):
    help = "Seed LearnGrid demo sample data for course-service."

    def add_arguments(self, parser) -> None:
        add_seed_arguments(parser, __file__)

    def handle(self, *args, **options) -> None:
        manifest = load_manifest(options["manifest"])
        records = [
            "courses",
            "categories",
            "tags",
            "learning_outcomes",
            "modules",
            "lessons",
            "topics",
            "course_revisions",
        ]
        if options["dry_run"]:
            planned(self, "course-service", manifest, records)
            return
        with transaction.atomic():
            if options["reset_sample_data"]:
                self.reset(manifest)
            self.seed(manifest)
        self.stdout.write(self.style.SUCCESS("Seeded course-service sample data."))

    def reset(self, manifest: dict) -> None:
        course_ids = [course_id(manifest, "prerequisite"), course_id(manifest, "main")]
        Course.objects.filter(id__in=course_ids).delete()
        CourseCategory.objects.filter(
            id=uuid_value(manifest["courses"]["main"]["category_id"])
        ).delete()
        CourseTag.objects.filter(id=uuid_value(manifest["courses"]["main"]["tag_id"])).delete()

    def seed(self, manifest: dict) -> None:
        published_at = now()
        prereq_data = manifest["courses"]["prerequisite"]
        prerequisite, _created = Course.objects.update_or_create(
            id=course_id(manifest, "prerequisite"),
            defaults={
                "institution_id": institution_id(manifest),
                "owner_profile_id": profile_id(manifest, "instructor"),
                "title": prereq_data["title"],
                "slug": prereq_data["slug"],
                "description": "Introductory orientation course for demo students.",
                "difficulty_level": CourseDifficulty.BEGINNER,
                "thumbnail_asset_id": None,
                "status": CourseStatus.PUBLISHED,
                "published_at": published_at,
                "deleted_at": None,
            },
        )

        category, _created = CourseCategory.objects.update_or_create(
            id=uuid_value(manifest["courses"]["main"]["category_id"]),
            defaults={
                "institution_id": institution_id(manifest),
                "name": "Learning Design",
                "slug": "learning-design",
                "parent_category": None,
            },
        )
        tag, _created = CourseTag.objects.update_or_create(
            id=uuid_value(manifest["courses"]["main"]["tag_id"]),
            defaults={
                "institution_id": institution_id(manifest),
                "name": "Demo",
                "slug": "demo",
            },
        )

        main_data = manifest["courses"]["main"]
        main_course, _created = Course.objects.update_or_create(
            id=course_id(manifest),
            defaults={
                "institution_id": institution_id(manifest),
                "owner_profile_id": profile_id(manifest, "instructor"),
                "title": main_data["title"],
                "slug": main_data["slug"],
                "description": "A populated demo course for local portal walkthroughs.",
                "difficulty_level": CourseDifficulty.BEGINNER,
                "thumbnail_asset_id": uuid_value(manifest["content"]["lesson_document"]["id"]),
                "status": CourseStatus.PUBLISHED,
                "published_at": published_at,
                "deleted_at": None,
            },
        )

        CourseCategoryLink.objects.update_or_create(course=main_course, category=category)
        CourseTagLink.objects.update_or_create(course=main_course, tag=tag)
        CoursePrerequisite.objects.update_or_create(
            course=main_course,
            prerequisite_course=prerequisite,
        )
        for position, description in enumerate(
            [
                "Explain how LearnGrid organizes courses, lessons, and activities.",
                "Complete a short quiz and assignment from a student portal.",
            ],
            start=1,
        ):
            LearningOutcome.objects.update_or_create(
                course=main_course,
                position=position,
                defaults={"description": description},
            )

        module, _created = CourseModule.objects.update_or_create(
            id=uuid_value(main_data["module_id"]),
            defaults={
                "course": main_course,
                "title": "Getting Started",
                "description": "Demo module for course structure screens.",
                "position": 1,
                "status": StructureStatus.PUBLISHED,
                "deleted_at": None,
            },
        )
        lesson, _created = Lesson.objects.update_or_create(
            id=uuid_value(main_data["lesson_id"]),
            defaults={
                "course": main_course,
                "module": module,
                "title": "Welcome to LearnGrid",
                "summary": "A seeded lesson connected to demo content assets.",
                "position": 1,
                "status": StructureStatus.PUBLISHED,
                "content_asset_id": uuid_value(manifest["content"]["lesson_document"]["id"]),
                "published_at": published_at,
                "deleted_at": None,
            },
        )
        Topic.objects.update_or_create(
            id=uuid_value(main_data["topic_id"]),
            defaults={
                "lesson": lesson,
                "title": "Demo lesson notes",
                "position": 1,
                "content_asset_id": uuid_value(manifest["content"]["lesson_video"]["id"]),
            },
        )
        CourseRevision.objects.update_or_create(
            id=uuid_value(main_data["revision_id"]),
            defaults={
                "course": main_course,
                "version_number": 1,
                "snapshot": {
                    "course": main_course.title,
                    "modules": [{"title": module.title, "lessons": [lesson.title]}],
                },
                "created_by_profile_id": profile_id(manifest, "instructor"),
            },
        )
