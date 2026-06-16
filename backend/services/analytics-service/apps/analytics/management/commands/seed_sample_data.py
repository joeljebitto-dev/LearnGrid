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
    institution_id,
    load_manifest,
    now,
    planned,
    profile_id,
    today,
    uuid_value,
)

from apps.analytics.models import (  # noqa: E402
    DashboardAggregate,
    DashboardScopeType,
    EventFact,
    ReportSnapshot,
    ReportType,
    SearchIndexRecord,
    SearchResourceType,
    UsageMetric,
)


class Command(BaseCommand):
    help = "Seed LearnGrid demo sample data for analytics-service."

    def add_arguments(self, parser) -> None:
        add_seed_arguments(parser, __file__)

    def handle(self, *args, **options) -> None:
        manifest = load_manifest(options["manifest"])
        records = [
            "event_facts",
            "dashboard_aggregates",
            "usage_metrics",
            "report_snapshots",
            "search_index_records",
        ]
        if options["dry_run"]:
            planned(self, "analytics-service", manifest, records)
            return
        with transaction.atomic():
            if options["reset_sample_data"]:
                self.reset(manifest)
            self.seed(manifest)
        self.stdout.write(self.style.SUCCESS("Seeded analytics-service sample data."))

    def reset(self, manifest: dict) -> None:
        data = manifest["analytics"]
        EventFact.objects.filter(id=uuid_value(data["event_fact_id"])).delete()
        DashboardAggregate.objects.filter(
            id__in=[
                uuid_value(data["student_aggregate_id"]),
                uuid_value(data["instructor_aggregate_id"]),
                uuid_value(data["institution_aggregate_id"]),
            ]
        ).delete()
        ReportSnapshot.objects.filter(id=uuid_value(data["report_snapshot_id"])).delete()
        UsageMetric.objects.filter(id=uuid_value(data["usage_metric_id"])).delete()
        SearchIndexRecord.objects.filter(
            id__in=[uuid_value(data["course_search_id"]), uuid_value(data["user_search_id"])]
        ).delete()

    def seed(self, manifest: dict) -> None:
        data = manifest["analytics"]
        current_time = now()
        metric_date = today()
        EventFact.objects.update_or_create(
            id=uuid_value(data["event_fact_id"]),
            defaults={
                "event_id": uuid_value(data["event_fact_id"]),
                "event_type": "CourseCompleted",
                "producer_service": "progress-service",
                "aggregate_id": course_id(manifest),
                "institution_id": institution_id(manifest),
                "occurred_at": current_time,
                "payload": {
                    "seed_namespace": manifest["seed_namespace"],
                    "student_profile_id": str(profile_id(manifest, "student")),
                    "course_id": str(course_id(manifest)),
                },
            },
        )
        DashboardAggregate.objects.update_or_create(
            id=uuid_value(data["student_aggregate_id"]),
            defaults={
                "scope_type": DashboardScopeType.STUDENT,
                "scope_id": profile_id(manifest, "student"),
                "metric_date": metric_date,
                "metrics": {
                    "active_courses": [
                        {
                            "course_id": str(course_id(manifest)),
                            "title": manifest["courses"]["main"]["title"],
                        }
                    ],
                    "completed_lessons": [
                        {
                            "lesson_id": manifest["courses"]["main"]["lesson_id"],
                            "title": "Welcome to LearnGrid",
                        }
                    ],
                    "pending_assessments": [],
                    "grades": [
                        {
                            "course_id": str(course_id(manifest)),
                            "score": 90,
                            "max_score": 100,
                        }
                    ],
                    "upcoming_deadlines": [
                        {"title": "Demo Reflection Assignment", "due_in_days": 14}
                    ],
                    "summary": {
                        "active_courses": 1,
                        "completion_percent": 100,
                        "average_grade": 90,
                    },
                },
                "computed_at": current_time,
            },
        )
        DashboardAggregate.objects.update_or_create(
            id=uuid_value(data["instructor_aggregate_id"]),
            defaults={
                "scope_type": DashboardScopeType.INSTRUCTOR,
                "scope_id": profile_id(manifest, "instructor"),
                "metric_date": metric_date,
                "metrics": {
                    "learner_engagement": [{"label": "Demo course", "active_learners": 1}],
                    "progress_distribution": [{"bucket": "completed", "count": 1}],
                    "assessment_status": [{"status": "graded", "count": 1}],
                    "course_summaries": [
                        {
                            "course_id": str(course_id(manifest)),
                            "title": manifest["courses"]["main"]["title"],
                            "completion_percent": 100,
                        }
                    ],
                    "summary": {"assigned_courses": 1, "active_learners": 1, "pending_reviews": 0},
                },
                "computed_at": current_time,
            },
        )
        DashboardAggregate.objects.update_or_create(
            id=uuid_value(data["institution_aggregate_id"]),
            defaults={
                "scope_type": DashboardScopeType.INSTITUTION,
                "scope_id": institution_id(manifest),
                "metric_date": metric_date,
                "metrics": {
                    "active_users": 4,
                    "enrollments": 1,
                    "completion_rates": [
                        {"course_id": str(course_id(manifest)), "completion_percent": 100}
                    ],
                    "assessment_results": [
                        {"assessment": "Demo Knowledge Check", "average_score": 90}
                    ],
                    "system_usage": {"events": 1, "reports": 1},
                    "summary": {"active_users": 4, "courses": 1, "certificates": 1},
                },
                "computed_at": current_time,
            },
        )
        ReportSnapshot.objects.update_or_create(
            id=uuid_value(data["report_snapshot_id"]),
            defaults={
                "institution_id": institution_id(manifest),
                "report_type": ReportType.DASHBOARD,
                "parameters": {"seed_namespace": manifest["seed_namespace"]},
                "result_payload": {"summary": {"active_users": 4, "completion_rate": 100}},
                "generated_by_profile_id": profile_id(manifest, "institution_admin"),
                "generated_at": current_time,
            },
        )
        UsageMetric.objects.update_or_create(
            id=uuid_value(data["usage_metric_id"]),
            defaults={
                "metric_name": "active_users",
                "metric_value": decimal_value("4.0000"),
                "scope_type": DashboardScopeType.INSTITUTION,
                "scope_id": institution_id(manifest),
                "bucket_start_at": current_time,
                "bucket_end_at": current_time,
            },
        )
        SearchIndexRecord.objects.update_or_create(
            id=uuid_value(data["course_search_id"]),
            defaults={
                "resource_type": SearchResourceType.COURSE,
                "resource_id": course_id(manifest),
                "institution_id": institution_id(manifest),
                "search_text": "Foundations of Web Learning demo course learning design",
                "metadata": {"seed_namespace": manifest["seed_namespace"], "status": "published"},
                "updated_at": current_time,
            },
        )
        SearchIndexRecord.objects.update_or_create(
            id=uuid_value(data["user_search_id"]),
            defaults={
                "resource_type": SearchResourceType.USER,
                "resource_id": profile_id(manifest, "student"),
                "institution_id": institution_id(manifest),
                "search_text": "Bot Student demo learner BOT-STU-001",
                "metadata": {
                    "seed_namespace": manifest["seed_namespace"],
                    "profile_type": "student",
                },
                "updated_at": current_time,
            },
        )
