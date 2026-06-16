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
    days_from_now,
    institution_id,
    load_manifest,
    planned,
    profile_id,
    uuid_value,
)

from apps.enrollments.models import (  # noqa: E402
    AccessGrant,
    AccessGrantStatus,
    BatchEnrollment,
    CohortEnrollment,
    Enrollment,
    EnrollmentHistory,
    EnrollmentJobStatus,
    EnrollmentStatus,
)


class Command(BaseCommand):
    help = "Seed LearnGrid demo sample data for enrollment-service."

    def add_arguments(self, parser) -> None:
        add_seed_arguments(parser, __file__)

    def handle(self, *args, **options) -> None:
        manifest = load_manifest(options["manifest"])
        records = [
            "enrollments",
            "batch_enrollments",
            "cohort_enrollments",
            "history",
            "access_grants",
        ]
        if options["dry_run"]:
            planned(self, "enrollment-service", manifest, records)
            return
        with transaction.atomic():
            if options["reset_sample_data"]:
                self.reset(manifest)
            self.seed(manifest)
        self.stdout.write(self.style.SUCCESS("Seeded enrollment-service sample data."))

    def reset(self, manifest: dict) -> None:
        data = manifest["enrollment"]
        Enrollment.objects.filter(id=uuid_value(data["id"])).delete()
        BatchEnrollment.objects.filter(id=uuid_value(data["batch_enrollment_id"])).delete()
        CohortEnrollment.objects.filter(id=uuid_value(data["cohort_enrollment_id"])).delete()

    def seed(self, manifest: dict) -> None:
        data = manifest["enrollment"]
        enrollment, _created = Enrollment.objects.update_or_create(
            id=uuid_value(data["id"]),
            defaults={
                "student_profile_id": profile_id(manifest, "student"),
                "course_id": course_id(manifest),
                "institution_id": institution_id(manifest),
                "status": EnrollmentStatus.ACTIVE,
                "enrolled_by_profile_id": profile_id(manifest, "institution_admin"),
                "completed_at": None,
                "expires_at": days_from_now(180),
            },
        )
        EnrollmentHistory.objects.update_or_create(
            id=uuid_value(data["history_id"]),
            defaults={
                "enrollment": enrollment,
                "from_status": None,
                "to_status": EnrollmentStatus.ACTIVE,
                "changed_by_profile_id": profile_id(manifest, "institution_admin"),
                "reason": "Seeded demo enrollment.",
            },
        )
        AccessGrant.objects.update_or_create(
            id=uuid_value(data["access_grant_id"]),
            defaults={
                "enrollment": enrollment,
                "student_profile_id": profile_id(manifest, "student"),
                "course_id": course_id(manifest),
                "access_status": AccessGrantStatus.ACTIVE,
                "valid_until": days_from_now(180),
            },
        )
        BatchEnrollment.objects.update_or_create(
            id=uuid_value(data["batch_enrollment_id"]),
            defaults={
                "batch_id": uuid_value(manifest["batch"]["id"]),
                "course_id": course_id(manifest),
                "requested_by_profile_id": profile_id(manifest, "institution_admin"),
                "status": EnrollmentJobStatus.COMPLETED,
                "summary": {"seed_namespace": manifest["seed_namespace"], "enrolled": 1},
            },
        )
        CohortEnrollment.objects.update_or_create(
            id=uuid_value(data["cohort_enrollment_id"]),
            defaults={
                "cohort_id": uuid_value(data["cohort_id"]),
                "course_id": course_id(manifest),
                "requested_by_profile_id": profile_id(manifest, "institution_admin"),
                "status": EnrollmentJobStatus.COMPLETED,
                "summary": {"seed_namespace": manifest["seed_namespace"], "enrolled": 1},
            },
        )
