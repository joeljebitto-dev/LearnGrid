from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

import jwt
import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.analytics import services, views
from apps.analytics.models import DashboardAggregate, DashboardScopeType, EventFact, ReportSnapshot


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def access_token():
    now = timezone.now()
    return jwt.encode(
        {
            "iss": settings.AUTH_JWT_ISSUER,
            "sub": str(uuid4()),
            "typ": "access",
            "jti": str(uuid4()),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
        settings.AUTH_JWT_SIGNING_KEY,
        algorithm=settings.AUTH_JWT_ALGORITHM,
    )


@pytest.fixture(autouse=True)
def allow_remote_authorization(monkeypatch):
    monkeypatch.setattr(services, "remote_authorization_check", lambda **_kwargs: True)


def auth_headers(token: str) -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def profile_payload(*, profile_type: str, profile_id=None, institution_id=None) -> dict:
    return {
        "id": str(profile_id or uuid4()),
        "auth_account_id": str(uuid4()),
        "institution_id": str(institution_id or uuid4()),
        "first_name": "Ada",
        "last_name": "Lovelace",
        "display_name": "Ada Lovelace",
        "avatar_url": None,
        "status": "active",
        "metadata": {},
        "profile_type": profile_type,
        "role_profile": {},
        "created_at": timezone.now().isoformat(),
        "updated_at": timezone.now().isoformat(),
        "deleted_at": None,
    }


@pytest.mark.django_db
def test_event_ingestion_is_idempotent(api_client, access_token):
    event_id = uuid4()
    payload = {
        "event_id": str(event_id),
        "event_type": "DashboardViewed",
        "producer_service": "frontend-service",
        "aggregate_id": str(uuid4()),
        "occurred_at": timezone.now().isoformat(),
        "payload": {"portal": "student"},
    }

    first_response = api_client.post(
        "/api/analytics/events/ingest/",
        payload,
        **auth_headers(access_token),
        format="json",
    )
    second_response = api_client.post(
        "/api/analytics/events/ingest/",
        payload,
        **auth_headers(access_token),
        format="json",
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 200
    assert first_response.json()["created"] is True
    assert second_response.json()["created"] is False
    assert EventFact.objects.filter(event_id=event_id).count() == 1


@pytest.mark.django_db
def test_student_dashboard_uses_current_profile_and_latest_aggregate(
    api_client,
    access_token,
    monkeypatch,
):
    profile_id = uuid4()
    profile = profile_payload(profile_type="student", profile_id=profile_id)
    monkeypatch.setattr(views, "current_profile", lambda **_kwargs: profile)
    DashboardAggregate.objects.create(
        scope_type=DashboardScopeType.STUDENT,
        scope_id=profile_id,
        metric_date=date.today(),
        metrics={
            "active_courses": [{"title": "Algebra"}],
            "summary": {"active_course_count": 1},
        },
    )

    response = api_client.get(
        f"/api/analytics/dashboards/student/?profile_id={uuid4()}",
        **auth_headers(access_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["portal"] == "student"
    assert body["profile"]["id"] == str(profile_id)
    assert body["active_courses"] == [{"title": "Algebra"}]
    assert body["summary"]["active_course_count"] == 1


@pytest.mark.django_db
def test_empty_student_dashboard_returns_zero_payload(api_client, access_token, monkeypatch):
    profile = profile_payload(profile_type="student")
    monkeypatch.setattr(views, "current_profile", lambda **_kwargs: profile)

    response = api_client.get(
        "/api/analytics/dashboards/student/",
        **auth_headers(access_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["aggregate"] is None
    assert body["active_courses"] == []
    assert body["summary"]["active_course_count"] == 0


@pytest.mark.django_db
def test_instructor_dashboard_requires_instructor_profile(api_client, access_token, monkeypatch):
    profile = profile_payload(profile_type="student")
    monkeypatch.setattr(views, "current_profile", lambda **_kwargs: profile)

    response = api_client.get(
        "/api/analytics/dashboards/instructor/",
        **auth_headers(access_token),
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_dashboard_enforces_institution_scope(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    checks = []

    def remote_authorization_check(**kwargs):
        checks.append(kwargs)
        return True

    monkeypatch.setattr(services, "remote_authorization_check", remote_authorization_check)

    response = api_client.get(
        f"/api/analytics/dashboards/admin/?institution_id={institution_id}",
        **auth_headers(access_token),
    )

    assert response.status_code == 200
    assert checks[0]["permission"] == "analytics.view"
    assert checks[0]["scope_type"] == "institution"
    assert checks[0]["scope_id"] == str(institution_id)


@pytest.mark.django_db
def test_admin_dashboard_denies_failed_authorization(api_client, access_token, monkeypatch):
    monkeypatch.setattr(services, "remote_authorization_check", lambda **_kwargs: False)

    response = api_client.get(
        f"/api/analytics/dashboards/admin/?institution_id={uuid4()}",
        **auth_headers(access_token),
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_report_snapshots_create_and_list_with_authorization(
    api_client,
    access_token,
    monkeypatch,
):
    institution_id = uuid4()
    profile_id = uuid4()
    monkeypatch.setattr(
        views,
        "current_profile",
        lambda **_kwargs: profile_payload(
            profile_type="admin",
            profile_id=profile_id,
            institution_id=institution_id,
        ),
    )

    create_response = api_client.post(
        "/api/analytics/reports/snapshots/",
        {
            "institution_id": str(institution_id),
            "report_type": "dashboard",
            "parameters": {"range": "7d"},
            "result_payload": {"summary": {"active_user_count": 12}},
        },
        **auth_headers(access_token),
        format="json",
    )
    list_response = api_client.get(
        f"/api/analytics/reports/snapshots/?institution_id={institution_id}",
        **auth_headers(access_token),
    )

    assert create_response.status_code == 201
    assert list_response.status_code == 200
    assert ReportSnapshot.objects.count() == 1
    assert create_response.json()["generated_by_profile_id"] == str(profile_id)
    assert list_response.json()["count"] == 1
