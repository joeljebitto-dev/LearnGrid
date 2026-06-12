from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urljoin

import pytest
import requests
from jsonschema import validate


ROOT = Path(__file__).resolve().parents[2]

SERVICE_API_PREFIXES = {
    "auth-service": "/api/auth/",
    "user-service": "/api/users/",
    "course-service": "/api/courses/",
    "content-service": "/api/content/",
    "enrollment-service": "/api/enrollments/",
    "progress-service": "/api/progress/",
    "assessment-service": "/api/assessments/",
    "grading-service": "/api/grading/",
    "notification-service": "/api/notifications/",
    "analytics-service": "/api/analytics/",
}

EXPECTED_ROUTE_FRAGMENTS = {
    "auth-service": [
        "token/issue/",
        "token/refresh/",
        "password-reset/request/",
        "password-reset/confirm/",
        "authorization/check/",
    ],
    "user-service": [
        "profiles/",
        "profiles/me/",
        "institutions/",
        "departments/",
        "batches/",
    ],
    "course-service": [
        "<uuid:course_id>/structure/",
        "<uuid:course_id>/modules/reorder/",
        "lessons/<uuid:lesson_id>/topics/reorder/",
        "categories/",
        "tags/",
    ],
    "content-service": [
        "assets/uploads/presigned/",
        "assets/uploads/proxy/",
        "assets/<uuid:asset_id>/uploads/complete/",
        "assets/<uuid:asset_id>/access/",
        "download/<uuid:access_id>/",
    ],
    "enrollment-service": [
        "access/check/",
        "batch-enrollments/",
        "cohort-enrollments/",
        "<uuid:enrollment_id>/transition/",
        "<uuid:enrollment_id>/history/",
    ],
    "progress-service": [
        "lessons/",
        "videos/",
        "assessments/",
        "courses/",
        "events/",
    ],
    "assessment-service": [
        "question-banks/",
        "<uuid:assessment_id>/attempts/start/",
        "attempts/<uuid:attempt_id>/submit/",
        "assignments/<uuid:assignment_id>/submissions/",
        "grading/quiz-attempts/<uuid:attempt_id>/",
    ],
    "grading-service": [
        "rules/",
        "records/calculate/",
        "records/<uuid:grade_record_id>/publish/",
        "results/",
        "certificates/eligibility/evaluate/",
    ],
    "notification-service": [
        "templates/",
        "<uuid:notification_id>/read/",
        "read-all/",
        "preferences/",
        "events/ingest/",
    ],
    "analytics-service": [
        "dashboards/student/",
        "dashboards/admin/system/",
        "search/index-records/",
        "reports/snapshots/",
        "reports/generate/",
    ],
}

MINIMAL_OPENAPI_SCHEMA = {
    "type": "object",
    "required": ["openapi", "info", "paths"],
    "properties": {
        "openapi": {"type": "string", "pattern": "^3\\."},
        "info": {
            "type": "object",
            "required": ["title", "version"],
            "properties": {
                "title": {"type": "string"},
                "version": {"type": "string"},
            },
        },
        "paths": {"type": "object"},
    },
}


@pytest.mark.parametrize(("service", "api_prefix"), SERVICE_API_PREFIXES.items())
def test_service_declares_openapi_contract(service: str, api_prefix: str):
    service_root = ROOT / "backend" / "services" / service
    settings = (service_root / "config" / "settings" / "base.py").read_text(encoding="utf-8")
    urls = (service_root / "config" / "urls.py").read_text(encoding="utf-8")
    pyproject = (service_root / "pyproject.toml").read_text(encoding="utf-8")

    assert 'drf-spectacular = "' in pyproject
    assert '"drf_spectacular"' in settings
    assert '"DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema"' in settings
    assert "SPECTACULAR_SETTINGS" in settings
    assert 'path("api/schema/"' in urls
    assert 'path("api/docs/"' in urls
    assert api_prefix.lstrip("/") in urls


@pytest.mark.parametrize(("service", "expected_fragments"), EXPECTED_ROUTE_FRAGMENTS.items())
def test_service_declares_required_product_routes(service: str, expected_fragments: list[str]):
    service_root = ROOT / "backend" / "services" / service
    app_url_files = list((service_root / "apps").glob("*/urls.py"))
    assert len(app_url_files) == 1

    app_urls = app_url_files[0].read_text(encoding="utf-8")
    for fragment in expected_fragments:
        assert fragment in app_urls


def _live_contract_urls() -> dict[str, str]:
    raw = os.getenv("CONTRACT_SERVICE_URLS", "").strip()
    if not raw:
        return {}
    if raw.startswith("{"):
        return json.loads(raw)
    pairs = [part.strip() for part in raw.split(",") if part.strip()]
    return dict(pair.split("=", 1) for pair in pairs)


@pytest.mark.parametrize("service", sorted(SERVICE_API_PREFIXES))
def test_live_openapi_contract_when_service_urls_are_configured(service: str):
    service_urls = _live_contract_urls()
    if service not in service_urls:
        pytest.skip("Set CONTRACT_SERVICE_URLS to run live OpenAPI contract checks.")

    response = requests.get(urljoin(service_urls[service].rstrip("/") + "/", "api/schema/"), timeout=10)
    assert response.status_code == 200
    schema = response.json()
    validate(instance=schema, schema=MINIMAL_OPENAPI_SCHEMA)
    assert any(path.startswith(SERVICE_API_PREFIXES[service]) for path in schema["paths"])
