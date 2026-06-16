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

from apps.grading.models import (  # noqa: E402
    Certificate,
    CertificateEligibility,
    GradeHistory,
    GradeRecord,
    GradeRecordStatus,
    GradingRule,
    GradingRuleType,
    ManualReview,
    ManualReviewStatus,
    PublishedResult,
)


class Command(BaseCommand):
    help = "Seed LearnGrid demo sample data for grading-service."

    def add_arguments(self, parser) -> None:
        add_seed_arguments(parser, __file__)

    def handle(self, *args, **options) -> None:
        manifest = load_manifest(options["manifest"])
        records = [
            "grading_rules",
            "grade_records",
            "manual_reviews",
            "grade_history",
            "published_results",
            "certificate_eligibility",
            "certificates",
        ]
        if options["dry_run"]:
            planned(self, "grading-service", manifest, records)
            return
        with transaction.atomic():
            if options["reset_sample_data"]:
                self.reset(manifest)
            self.seed(manifest)
        self.stdout.write(self.style.SUCCESS("Seeded grading-service sample data."))

    def reset(self, manifest: dict) -> None:
        data = manifest["grading"]
        Certificate.objects.filter(id=uuid_value(data["certificate_id"])).delete()
        CertificateEligibility.objects.filter(id=uuid_value(data["eligibility_id"])).delete()
        PublishedResult.objects.filter(id=uuid_value(data["published_result_id"])).delete()
        GradeHistory.objects.filter(id=uuid_value(data["history_id"])).delete()
        ManualReview.objects.filter(id=uuid_value(data["manual_review_id"])).delete()
        GradeRecord.objects.filter(
            id__in=[uuid_value(data["quiz_grade_id"]), uuid_value(data["assignment_grade_id"])]
        ).delete()
        GradingRule.objects.filter(id=uuid_value(data["rule_id"])).delete()

    def seed(self, manifest: dict) -> None:
        data = manifest["grading"]
        current_time = now()
        GradingRule.objects.update_or_create(
            id=uuid_value(data["rule_id"]),
            defaults={
                "course_id": course_id(manifest),
                "assessment_id": None,
                "rule_type": GradingRuleType.WEIGHTED,
                "configuration": {
                    "seed_namespace": manifest["seed_namespace"],
                    "certificate_min_percent": 70,
                },
                "created_by_profile_id": profile_id(manifest, "instructor"),
            },
        )
        quiz_grade, _created = GradeRecord.objects.update_or_create(
            id=uuid_value(data["quiz_grade_id"]),
            defaults={
                "student_profile_id": profile_id(manifest, "student"),
                "course_id": course_id(manifest),
                "assessment_id": uuid_value(manifest["assessment"]["quiz_assessment_id"]),
                "submission_id": uuid_value(manifest["assessment"]["quiz_attempt_id"]),
                "score": decimal_value("90.00"),
                "max_score": decimal_value("100.00"),
                "status": GradeRecordStatus.PUBLISHED,
                "published_at": current_time,
            },
        )
        assignment_grade, _created = GradeRecord.objects.update_or_create(
            id=uuid_value(data["assignment_grade_id"]),
            defaults={
                "student_profile_id": profile_id(manifest, "student"),
                "course_id": course_id(manifest),
                "assessment_id": uuid_value(manifest["assessment"]["assignment_assessment_id"]),
                "submission_id": uuid_value(manifest["assessment"]["assignment_submission_id"]),
                "score": decimal_value("88.00"),
                "max_score": decimal_value("100.00"),
                "status": GradeRecordStatus.REVIEWED,
                "published_at": None,
            },
        )
        ManualReview.objects.update_or_create(
            id=uuid_value(data["manual_review_id"]),
            defaults={
                "grade_record": assignment_grade,
                "reviewer_profile_id": profile_id(manifest, "instructor"),
                "status": ManualReviewStatus.COMPLETED,
                "feedback": "Seeded review feedback for local demo.",
                "reviewed_at": current_time,
            },
        )
        GradeHistory.objects.update_or_create(
            id=uuid_value(data["history_id"]),
            defaults={
                "grade_record": assignment_grade,
                "previous_score": decimal_value("85.00"),
                "new_score": decimal_value("88.00"),
                "changed_by_profile_id": profile_id(manifest, "instructor"),
                "change_reason": "Seeded manual review adjustment.",
            },
        )
        PublishedResult.objects.update_or_create(
            id=uuid_value(data["published_result_id"]),
            defaults={
                "grade_record": quiz_grade,
                "student_profile_id": profile_id(manifest, "student"),
                "course_id": course_id(manifest),
                "published_score": decimal_value("90.00"),
                "published_feedback": "Seeded published quiz result.",
                "published_by_profile_id": profile_id(manifest, "instructor"),
            },
        )
        eligibility, _created = CertificateEligibility.objects.update_or_create(
            id=uuid_value(data["eligibility_id"]),
            defaults={
                "student_profile_id": profile_id(manifest, "student"),
                "course_id": course_id(manifest),
                "eligible": True,
                "reason": "seeded_eligible",
            },
        )
        Certificate.objects.update_or_create(
            id=uuid_value(data["certificate_id"]),
            defaults={
                "certificate_eligibility": eligibility,
                "student_profile_id": profile_id(manifest, "student"),
                "course_id": course_id(manifest),
                "certificate_number": data["certificate_number"],
                "certificate_asset_id": None,
                "revoked_at": None,
            },
        )

