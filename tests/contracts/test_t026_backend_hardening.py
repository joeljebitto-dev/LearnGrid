from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

NON_AUTH_SERVICES = [
    "user-service",
    "course-service",
    "content-service",
    "enrollment-service",
    "progress-service",
    "assessment-service",
    "grading-service",
    "notification-service",
    "analytics-service",
]

SERVICE_DOMAINS = {
    "user-service": "users",
    "course-service": "courses",
    "content-service": "content",
    "enrollment-service": "enrollments",
    "progress-service": "progress",
    "assessment-service": "assessments",
    "grading-service": "grading",
    "notification-service": "notifications",
    "analytics-service": "analytics",
}

HARDENING_DOCS = [
    "README.md",
    "HARD-026-api-completeness.md",
    "HARD-026-authorization-tenant-isolation.md",
    "HARD-026-eventing-async.md",
    "HARD-026-analytics-notifications-certificates-content.md",
    "HARD-026-migrations-retention-compliance.md",
]


def test_backend_hardening_evidence_docs_exist():
    hardening_root = ROOT / "docs" / "backend-hardening"

    for relative_path in HARDENING_DOCS:
        path = hardening_root / relative_path
        assert path.exists(), f"Missing backend hardening evidence doc: {path}"
        assert "T-026" in path.read_text(encoding="utf-8")


def test_non_auth_services_use_shared_authorization_helper():
    for service in NON_AUTH_SERVICES:
        service_root = ROOT / "backend" / "services" / service
        domain = SERVICE_DOMAINS[service]
        pyproject = (service_root / "pyproject.toml").read_text(encoding="utf-8")
        settings = (service_root / "config" / "settings" / "base.py").read_text(
            encoding="utf-8"
        )
        permissions = (
            service_root / "apps" / domain / "permissions.py"
        ).read_text(encoding="utf-8")

        assert (
            'learngrid-authz = { path = "../../shared/learngrid-authz", develop = true }'
            in pyproject
        )
        assert "AUTHORIZATION_CHECK_TIMEOUT_SECONDS" in settings
        assert "from learngrid_authz import" in permissions
        assert "urlrequest.urlopen" not in permissions
        assert "urllib" not in permissions
        assert "AUTH_SERVICE_BASE_URL" not in permissions


def test_top_level_api_views_use_standard_pagination_limits():
    for service in NON_AUTH_SERVICES:
        service_root = ROOT / "backend" / "services" / service
        domain = SERVICE_DOMAINS[service]
        views = (service_root / "apps" / domain / "views.py").read_text(encoding="utf-8")

        assert "PageNumberPagination" in views
        assert 'page_size_query_param = "page_size"' in views
        assert "max_page_size = 100" in views


def test_data_migrations_define_reverse_operations():
    migration_files = sorted((ROOT / "backend" / "services").glob("*/apps/*/migrations/*.py"))
    for migration in migration_files:
        text = migration.read_text(encoding="utf-8")
        if "migrations.RunPython(" in text:
            assert (
                "reverse_code" in text
                or "migrations.RunPython.noop" in text
                or ", un" in text
                or ", drop_" in text
            )
        if "migrations.RunSQL(" in text:
            assert "reverse_sql" in text or "migrations.RunSQL.noop" in text
