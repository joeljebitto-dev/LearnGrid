from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

import jwt
import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.analytics import services, views
from apps.analytics.models import (
    DashboardAggregate,
    EventFact,
    ReportSnapshot,
    SearchIndexRecord,
    UsageMetric,
)


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


def profile_payload(profile_id=None) -> dict:
    return {
        "id": str(profile_id or uuid4()),
        "auth_account_id": str(uuid4()),
        "institution_id": str(uuid4()),
        "first_name": "Grace",
        "last_name": "Hopper",
        "display_name": "Grace Hopper",
        "avatar_url": None,
        "status": "active",
        "metadata": {},
        "profile_type": "admin",
        "role_profile": {},
        "created_at": timezone.now().isoformat(),
        "updated_at": timezone.now().isoformat(),
        "deleted_at": None,
    }


@pytest.mark.django_db
def test_search_returns_only_resource_types_allowed_by_scope(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    SearchIndexRecord.objects.create(
        resource_type="course",
        resource_id=uuid4(),
        institution_id=institution_id,
        search_text="Intro to Algebra",
        metadata={"status": "published"},
    )
    SearchIndexRecord.objects.create(
        resource_type="user",
        resource_id=uuid4(),
        institution_id=institution_id,
        search_text="Student Algebra User",
        metadata={"status": "active", "profile_type": "student"},
    )

    def remote_authorization_check(**kwargs):
        return kwargs["permission"] == "course.view"

    monkeypatch.setattr(services, "remote_authorization_check", remote_authorization_check)

    response = api_client.get(
        f"/api/analytics/search/?institution_id={institution_id}&q=Algebra",
        **auth_headers(access_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["results"][0]["resource_type"] == "course"


@pytest.mark.django_db
def test_resource_search_denies_failed_remote_authorization(api_client, access_token, monkeypatch):
    monkeypatch.setattr(services, "remote_authorization_check", lambda **_kwargs: False)

    response = api_client.get(
        "/api/analytics/search/users/",
        **auth_headers(access_token),
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_search_index_upsert_and_delete(api_client, access_token):
    resource_id = uuid4()
    payload = {
        "resource_type": "assessment",
        "resource_id": str(resource_id),
        "institution_id": str(uuid4()),
        "search_text": "Midterm assessment",
        "metadata": {"status": "published", "assessment_type": "quiz"},
    }

    create_response = api_client.post(
        "/api/analytics/search/index-records/",
        payload,
        **auth_headers(access_token),
        format="json",
    )
    update_response = api_client.post(
        "/api/analytics/search/index-records/",
        {**payload, "search_text": "Updated midterm assessment"},
        **auth_headers(access_token),
        format="json",
    )
    delete_response = api_client.delete(
        f"/api/analytics/search/index-records/assessment/{resource_id}/",
        **auth_headers(access_token),
    )

    assert create_response.status_code == 201
    assert create_response.json()["created"] is True
    assert update_response.status_code == 200
    assert update_response.json()["created"] is False
    assert delete_response.status_code == 204
    assert SearchIndexRecord.objects.count() == 0


@pytest.mark.django_db
def test_dashboard_aggregate_and_usage_metric_endpoints(api_client, access_token):
    institution_id = uuid4()

    aggregate_response = api_client.post(
        "/api/analytics/dashboards/aggregates/",
        {
            "scope_type": "institution",
            "scope_id": str(institution_id),
            "metric_date": date.today().isoformat(),
            "metrics": {"summary": {"active_user_count": 4}},
        },
        **auth_headers(access_token),
        format="json",
    )
    metric_response = api_client.post(
        "/api/analytics/usage-metrics/",
        {
            "metric_name": "course_completion_percent",
            "metric_value": "82.5000",
            "scope_type": "institution",
            "scope_id": str(institution_id),
            "bucket_start_at": timezone.now().isoformat(),
            "bucket_end_at": timezone.now().isoformat(),
        },
        **auth_headers(access_token),
        format="json",
    )
    aggregate_list_response = api_client.get(
        f"/api/analytics/dashboards/aggregates/?institution_id={institution_id}",
        **auth_headers(access_token),
    )
    metric_list_response = api_client.get(
        f"/api/analytics/usage-metrics/?scope_type=institution&scope_id={institution_id}",
        **auth_headers(access_token),
    )

    assert aggregate_response.status_code == 201
    assert metric_response.status_code == 201
    assert aggregate_list_response.json()["count"] == 1
    assert metric_list_response.json()["count"] == 1
    assert DashboardAggregate.objects.count() == 1
    assert UsageMetric.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "report_type",
    [
        "active_users",
        "enrollments",
        "completion_rates",
        "assessment_results",
        "system_usage",
    ],
)
def test_report_generation_uses_analytics_db_inputs(
    api_client,
    access_token,
    monkeypatch,
    report_type,
):
    institution_id = uuid4()
    profile_id = uuid4()
    monkeypatch.setattr(views, "current_profile", lambda **_kwargs: profile_payload(profile_id))
    SearchIndexRecord.objects.create(
        resource_type="user",
        resource_id=uuid4(),
        institution_id=institution_id,
        search_text="Active student",
        metadata={"status": "active", "profile_type": "student"},
    )
    SearchIndexRecord.objects.create(
        resource_type="enrollment",
        resource_id=uuid4(),
        institution_id=institution_id,
        search_text="Student enrolled",
        metadata={"status": "active"},
    )
    SearchIndexRecord.objects.create(
        resource_type="submission",
        resource_id=uuid4(),
        institution_id=institution_id,
        search_text="Quiz submitted",
        metadata={"submission_status": "submitted"},
    )
    now = timezone.now()
    UsageMetric.objects.create(
        metric_name="course_completion_percent",
        metric_value="75.0000",
        scope_type="institution",
        scope_id=institution_id,
        bucket_start_at=now,
        bucket_end_at=now,
    )
    UsageMetric.objects.create(
        metric_name="assessment_score_percent",
        metric_value="91.0000",
        scope_type="institution",
        scope_id=institution_id,
        bucket_start_at=now,
        bucket_end_at=now,
    )
    EventFact.objects.create(
        event_id=uuid4(),
        event_type="CourseCompleted",
        producer_service="progress-service",
        aggregate_id=uuid4(),
        institution_id=institution_id,
        occurred_at=now,
        payload={},
    )

    response = api_client.post(
        "/api/analytics/reports/generate/",
        {
            "institution_id": str(institution_id),
            "report_type": report_type,
            "parameters": {},
        },
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["report_type"] == report_type
    assert body["generated_by_profile_id"] == str(profile_id)
    assert body["result_payload"]["report_type"] == report_type
    assert "summary" in body["result_payload"]
    assert ReportSnapshot.objects.count() == 1
