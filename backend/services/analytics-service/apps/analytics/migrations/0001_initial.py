# Generated for LearnGrid LMS T-011 dashboards and portals.

import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DashboardAggregate",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "scope_type",
                    models.CharField(
                        choices=[
                            ("student", "Student"),
                            ("instructor", "Instructor"),
                            ("institution", "Institution"),
                            ("course", "Course"),
                            ("platform", "Platform"),
                        ],
                        max_length=32,
                    ),
                ),
                ("scope_id", models.UUIDField()),
                ("metric_date", models.DateField()),
                ("metrics", models.JSONField(default=dict)),
                ("computed_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "db_table": "dashboard_aggregates",
            },
        ),
        migrations.CreateModel(
            name="EventFact",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("event_id", models.UUIDField(unique=True)),
                ("event_type", models.CharField(max_length=80)),
                ("producer_service", models.CharField(max_length=80)),
                ("aggregate_id", models.UUIDField()),
                ("institution_id", models.UUIDField(blank=True, null=True)),
                ("occurred_at", models.DateTimeField()),
                ("payload", models.JSONField(default=dict)),
                ("ingested_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "db_table": "event_facts",
            },
        ),
        migrations.CreateModel(
            name="ReportSnapshot",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("institution_id", models.UUIDField(blank=True, null=True)),
                (
                    "report_type",
                    models.CharField(
                        choices=[
                            ("active_users", "Active users"),
                            ("enrollments", "Enrollments"),
                            ("completion_rates", "Completion rates"),
                            ("assessment_results", "Assessment results"),
                            ("system_usage", "System usage"),
                            ("dashboard", "Dashboard"),
                        ],
                        max_length=80,
                    ),
                ),
                ("parameters", models.JSONField(default=dict)),
                ("result_payload", models.JSONField(default=dict)),
                ("generated_by_profile_id", models.UUIDField(blank=True, null=True)),
                ("generated_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "db_table": "report_snapshots",
            },
        ),
        migrations.CreateModel(
            name="SearchIndexRecord",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "resource_type",
                    models.CharField(
                        choices=[
                            ("course", "Course"),
                            ("user", "User"),
                            ("enrollment", "Enrollment"),
                            ("assessment", "Assessment"),
                            ("submission", "Submission"),
                        ],
                        max_length=64,
                    ),
                ),
                ("resource_id", models.UUIDField()),
                ("institution_id", models.UUIDField(blank=True, null=True)),
                ("search_text", models.TextField()),
                ("metadata", models.JSONField(default=dict)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "db_table": "search_index_records",
            },
        ),
        migrations.CreateModel(
            name="UsageMetric",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("metric_name", models.CharField(max_length=128)),
                ("metric_value", models.DecimalField(decimal_places=4, max_digits=18)),
                ("scope_type", models.CharField(blank=True, max_length=32, null=True)),
                ("scope_id", models.UUIDField(blank=True, null=True)),
                ("bucket_start_at", models.DateTimeField()),
                ("bucket_end_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "db_table": "usage_metrics",
            },
        ),
        migrations.AddConstraint(
            model_name="dashboardaggregate",
            constraint=models.UniqueConstraint(
                fields=("scope_type", "scope_id", "metric_date"),
                name="uq_dash_aggr_scope_date",
            ),
        ),
        migrations.AddIndex(
            model_name="dashboardaggregate",
            index=models.Index(fields=["scope_type"], name="idx_dash_aggr_scope_type"),
        ),
        migrations.AddIndex(
            model_name="eventfact",
            index=models.Index(fields=["event_type", "occurred_at"], name="idx_event_facts_type_time"),
        ),
        migrations.AddIndex(
            model_name="eventfact",
            index=models.Index(
                fields=["institution_id", "occurred_at"],
                name="idx_event_facts_inst_time",
            ),
        ),
        migrations.AddIndex(
            model_name="eventfact",
            index=models.Index(fields=["aggregate_id"], name="idx_event_facts_aggregate_id"),
        ),
        migrations.AddIndex(
            model_name="reportsnapshot",
            index=models.Index(
                fields=["institution_id", "report_type"],
                name="idx_report_snap_inst_type",
            ),
        ),
        migrations.AddIndex(
            model_name="reportsnapshot",
            index=models.Index(fields=["generated_at"], name="idx_report_snap_generated"),
        ),
        migrations.AddConstraint(
            model_name="searchindexrecord",
            constraint=models.UniqueConstraint(
                fields=("resource_type", "resource_id"),
                name="uq_search_index_resource",
            ),
        ),
        migrations.AddIndex(
            model_name="searchindexrecord",
            index=models.Index(fields=["resource_type"], name="idx_search_index_resource_type"),
        ),
        migrations.AddIndex(
            model_name="searchindexrecord",
            index=models.Index(fields=["institution_id"], name="idx_search_index_institution"),
        ),
        migrations.AddIndex(
            model_name="usagemetric",
            index=models.Index(
                fields=["metric_name", "bucket_start_at"],
                name="idx_usage_metrics_name_bucket",
            ),
        ),
        migrations.AddIndex(
            model_name="usagemetric",
            index=models.Index(
                fields=["scope_type", "scope_id", "bucket_start_at"],
                name="idx_usage_metrics_scope_bucket",
            ),
        ),
    ]
