from datetime import timedelta
from uuid import UUID

import pytest
import redis
from django.contrib.auth.hashers import make_password
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.authentication import services
from apps.authentication.models import (
    Account,
    AccountStatus,
    BlacklistReason,
    Credential,
    RefreshToken,
    Role,
    RoleAssignment,
    TokenBlacklist,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def active_account():
    account = Account.objects.create(email="student@example.com", status=AccountStatus.ACTIVE)
    Credential.objects.create(account=account, password_hash=make_password("correct-password"))
    return account


def issue_tokens(api_client, password="correct-password"):
    response = api_client.post(
        "/api/auth/token/issue/",
        {"email": "student@example.com", "password": password, "device_label": "pytest"},
        format="json",
    )
    return response


def assert_token_pair_response(response):
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access", "refresh", "access_expires_at", "refresh_expires_at"}
    assert body["access"]
    assert body["refresh"]
    return body


@pytest.mark.django_db
def test_valid_token_issue_stores_refresh_hash(api_client, active_account):
    response = issue_tokens(api_client)
    body = assert_token_pair_response(response)

    refresh_record = RefreshToken.objects.get(account=active_account)
    assert refresh_record.token_hash != body["refresh"]
    assert refresh_record.token_hash == services.hash_token(body["refresh"])
    assert refresh_record.device_label == "pytest"


@pytest.mark.django_db
def test_access_token_authorizes_session(api_client, active_account):
    body = assert_token_pair_response(issue_tokens(api_client))

    response = api_client.get(
        "/api/auth/session/",
        HTTP_AUTHORIZATION=f"Bearer {body['access']}",
    )

    assert response.status_code == 200
    assert response.json() == {
        "account_id": str(active_account.id),
        "email": active_account.email,
        "status": AccountStatus.ACTIVE,
        "primary_role": None,
        "role_assignments": [],
    }


@pytest.mark.django_db
def test_session_returns_active_role_assignments_and_primary_role(api_client, active_account):
    instructor_role = Role.objects.get(code="instructor")
    student_role = Role.objects.get(code="student")
    RoleAssignment.objects.create(
        account=active_account,
        role=student_role,
        scope_type="institution",
        scope_id="11111111-1111-1111-1111-111111111111",
    )
    RoleAssignment.objects.create(
        account=active_account,
        role=instructor_role,
        scope_type="institution",
        scope_id="11111111-1111-1111-1111-111111111111",
    )
    body = assert_token_pair_response(issue_tokens(api_client))

    response = api_client.get(
        "/api/auth/session/",
        HTTP_AUTHORIZATION=f"Bearer {body['access']}",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["primary_role"] == "instructor"
    assert {assignment["role_code"] for assignment in payload["role_assignments"]} == {
        "student",
        "instructor",
    }


@pytest.mark.django_db
def test_refresh_rotates_token_and_rejects_old_refresh(api_client, active_account):
    body = assert_token_pair_response(issue_tokens(api_client))

    response = api_client.post(
        "/api/auth/token/refresh/",
        {"refresh": body["refresh"]},
        format="json",
    )
    refreshed_body = assert_token_pair_response(response)
    assert refreshed_body["refresh"] != body["refresh"]

    old_refresh = RefreshToken.objects.get(token_hash=services.hash_token(body["refresh"]))
    assert old_refresh.revoked_at is not None
    assert TokenBlacklist.objects.filter(
        token_jti=old_refresh.token_jti,
        reason=BlacklistReason.ROTATION,
    ).exists()

    response = api_client.post(
        "/api/auth/token/refresh/",
        {"refresh": body["refresh"]},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_logout_revokes_refresh_and_access(api_client, active_account):
    body = assert_token_pair_response(issue_tokens(api_client))

    response = api_client.post(
        "/api/auth/logout/",
        {"refresh": body["refresh"], "access": body["access"]},
        format="json",
    )

    assert response.status_code == 200
    assert response.json() == {"status": "revoked"}

    response = api_client.get(
        "/api/auth/session/",
        HTTP_AUTHORIZATION=f"Bearer {body['access']}",
    )
    assert response.status_code == 403

    refresh_record = RefreshToken.objects.get(token_hash=services.hash_token(body["refresh"]))
    assert refresh_record.revoked_at is not None


@pytest.mark.django_db
def test_malformed_token_is_rejected(api_client):
    response = api_client.get("/api/auth/session/", HTTP_AUTHORIZATION="Bearer not-a-jwt")

    assert response.status_code == 403


@pytest.mark.django_db
def test_expired_access_token_is_rejected(api_client, active_account):
    with override_settings(AUTH_ACCESS_TOKEN_LIFETIME_SECONDS=-1):
        body = assert_token_pair_response(issue_tokens(api_client))

    response = api_client.get(
        "/api/auth/session/",
        HTTP_AUTHORIZATION=f"Bearer {body['access']}",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_password_change_invalidates_existing_access_token(api_client, active_account):
    body = assert_token_pair_response(issue_tokens(api_client))
    credential = active_account.credential
    credential.password_changed_at = timezone.now() + timedelta(seconds=1)
    credential.save(update_fields=["password_changed_at"])

    response = api_client.get(
        "/api/auth/session/",
        HTTP_AUTHORIZATION=f"Bearer {body['access']}",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_account_level_revocation_invalidates_access_and_refresh(api_client, active_account):
    body = assert_token_pair_response(issue_tokens(api_client))

    services.revoke_account_tokens(active_account, reason=BlacklistReason.ADMIN_REVOKE)

    response = api_client.get(
        "/api/auth/session/",
        HTTP_AUTHORIZATION=f"Bearer {body['access']}",
    )
    assert response.status_code == 403

    response = api_client.post(
        "/api/auth/token/refresh/",
        {"refresh": body["refresh"]},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_redis_blacklist_write_and_check(monkeypatch, api_client, active_account):
    writes = {}

    class FakeRedis:
        def setex(self, key, ttl, value):
            writes[key] = (ttl, value)

        def exists(self, key):
            return int(key in writes)

        def incr(self, key):
            count = int(writes.get(key, (0, "0"))[1]) + 1
            writes[key] = (None, str(count))
            return count

        def expire(self, key, ttl):
            value = writes.get(key, (None, "0"))[1]
            writes[key] = (ttl, value)

        def ttl(self, key):
            return writes.get(key, (0, "0"))[0] or 0

    monkeypatch.setattr(services, "_redis_client", lambda: FakeRedis())
    body = assert_token_pair_response(issue_tokens(api_client))

    api_client.post(
        "/api/auth/logout/",
        {"refresh": body["refresh"], "access": body["access"]},
        format="json",
    )

    assert writes
    blacklisted_jti = TokenBlacklist.objects.first().token_jti
    assert services.is_token_blacklisted(blacklisted_jti)


@pytest.mark.django_db
def test_blacklist_check_falls_back_to_database(monkeypatch, active_account):
    class BrokenRedis:
        def exists(self, _key):
            raise redis.RedisError("redis unavailable")

    token_jti = UUID("11111111-1111-1111-1111-111111111111")
    TokenBlacklist.objects.create(
        token_jti=token_jti,
        account=active_account,
        reason=BlacklistReason.LOGOUT,
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    monkeypatch.setattr(services, "_redis_client", lambda: BrokenRedis())

    assert services.is_token_blacklisted(token_jti)
