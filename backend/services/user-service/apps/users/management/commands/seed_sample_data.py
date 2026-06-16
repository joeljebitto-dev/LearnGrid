from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

ROOT = Path(__file__).resolve().parents[7]
sys.path.append(str(ROOT / "scripts" / "sample_data"))

from seed_helpers import (  # noqa: E402
    account_id,
    add_seed_arguments,
    institution_id,
    load_manifest,
    planned,
    profile_id,
    seed_metadata,
    uuid_value,
)

from apps.users.models import (  # noqa: E402
    AdminProfile,
    AdminType,
    Batch,
    BatchStatus,
    Department,
    DepartmentStatus,
    Institution,
    InstitutionStatus,
    InstructorProfile,
    StudentProfile,
    UserProfile,
    UserProfileStatus,
)


class Command(BaseCommand):
    help = "Seed LearnGrid demo sample data for user-service."

    def add_arguments(self, parser) -> None:
        add_seed_arguments(parser, __file__)

    def handle(self, *args, **options) -> None:
        manifest = load_manifest(options["manifest"])
        records = ["institution", "departments", "batch", "user_profiles", "role_profiles"]
        if options["dry_run"]:
            planned(self, "user-service", manifest, records)
            return
        with transaction.atomic():
            if options["reset_sample_data"]:
                self.reset(manifest)
            self.seed(manifest)
        self.stdout.write(self.style.SUCCESS("Seeded user-service sample data."))

    def reset(self, manifest: dict) -> None:
        profile_ids = [profile_id(manifest, key) for key in manifest["accounts"]]
        StudentProfile.objects.filter(user_profile_id__in=profile_ids).delete()
        InstructorProfile.objects.filter(user_profile_id__in=profile_ids).delete()
        AdminProfile.objects.filter(user_profile_id__in=profile_ids).delete()
        UserProfile.objects.filter(id__in=profile_ids).delete()
        UserProfile.objects.filter(metadata__seed_namespace=manifest["seed_namespace"]).delete()
        Batch.objects.filter(id=uuid_value(manifest["batch"]["id"])).delete()
        Department.objects.filter(
            id__in=[uuid_value(data["id"]) for data in manifest["departments"].values()]
        ).delete()
        Institution.objects.filter(id=institution_id(manifest)).delete()
        Institution.objects.filter(code=manifest["institution"]["code"]).delete()

    def seed(self, manifest: dict) -> None:
        institution, _created = Institution.objects.update_or_create(
            id=institution_id(manifest),
            defaults={
                "name": manifest["institution"]["name"],
                "code": manifest["institution"]["code"],
                "status": InstitutionStatus.ACTIVE,
                "settings": seed_metadata("institution", timezone="UTC"),
                "deleted_at": None,
            },
        )

        departments = {}
        for key, data in manifest["departments"].items():
            departments[key], _created = Department.objects.update_or_create(
                id=uuid_value(data["id"]),
                defaults={
                    "institution": institution,
                    "name": data["name"],
                    "code": data["code"],
                    "status": DepartmentStatus.ACTIVE,
                    "deleted_at": None,
                },
            )

        batch, _created = Batch.objects.update_or_create(
            id=uuid_value(manifest["batch"]["id"]),
            defaults={
                "institution": institution,
                "department": departments["computer_science"],
                "name": manifest["batch"]["name"],
                "start_date": date(2026, 1, 1),
                "end_date": date(2026, 12, 31),
                "status": BatchStatus.ACTIVE,
                "deleted_at": None,
            },
        )

        profiles = {}
        for key, account_data in manifest["accounts"].items():
            data = manifest["profiles"][key]
            UserProfile.objects.filter(auth_account_id=account_id(manifest, key)).exclude(
                id=profile_id(manifest, key)
            ).delete()
            profile, _created = UserProfile.objects.update_or_create(
                id=profile_id(manifest, key),
                defaults={
                    "auth_account_id": account_id(manifest, key),
                    "institution": institution,
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "display_name": data["display_name"],
                    "avatar_url": None,
                    "status": UserProfileStatus.ACTIVE,
                    "metadata": seed_metadata(f"{key}-profile", role=account_data["role"]),
                    "deleted_at": None,
                },
            )
            profiles[key] = profile

        AdminProfile.objects.update_or_create(
            user_profile=profiles["super_admin"],
            defaults={
                "admin_type": AdminType.SUPER_ADMIN,
                "department": departments["academic_operations"],
            },
        )
        AdminProfile.objects.update_or_create(
            user_profile=profiles["institution_admin"],
            defaults={
                "admin_type": AdminType.INSTITUTION_ADMIN,
                "department": departments["academic_operations"],
            },
        )
        InstructorProfile.objects.update_or_create(
            user_profile=profiles["instructor"],
            defaults={
                "employee_number": manifest["profiles"]["instructor"]["employee_number"],
                "department": departments["computer_science"],
                "title": manifest["profiles"]["instructor"]["title"],
                "bio": "Demo instructor profile for local LearnGrid walkthroughs.",
            },
        )
        StudentProfile.objects.update_or_create(
            user_profile=profiles["student"],
            defaults={
                "student_number": manifest["profiles"]["student"]["student_number"],
                "batch": batch,
                "department": departments["computer_science"],
                "guardian_profile": None,
            },
        )
