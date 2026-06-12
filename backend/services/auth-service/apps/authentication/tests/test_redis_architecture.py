from __future__ import annotations

from datetime import timedelta

import pytest
import redis
from django.contrib.auth.hashers import check_password, make_password
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.authentication import services
from apps.authentication.models import (
    Account,
    AccountStatus,
    Credential,
    PasswordResetStatus,
    PasswordResetToken,
)


@pytest.fixture
def api_client():
    return APIClient()


def create_account(email: str = "reset@example.com") -> Account:
    account = Account.objects.create(email=email, status=AccountStatus.ACTIVE)
    Credential.objects.create(account=account, password_hash=make_password("old-password"))
    return account


@pytest.mark.django_db
def test_login_rate_limit_blocks_after_configured_window(api_client):
    create_account("limited@example.com")

    with override_settings(AUTH_LOGIN_RATE_LIMIT_COUNT=1):
        first = api_client.post(
            "/api/auth/token/issue/",
            {"email": "limited@example.com", "password": "wrong-password"},
            format="json",
        )
        second = api_client.post(
            "/api/auth/token/issue/",
            {"email": "limited@example.com", "password": "wrong-password"},
            format="json",
        )

    assert first.status_code == 403
    assert second.status_code == 429


@pytest.mark.django_db
def test_password_reset_request_confirm_and_reuse(api_client, fake_redis):
    account = create_account()

    with override_settings(AUTH_PASSWORD_RESET_DEBUG_RETURN_TOKEN=True):
        response = api_client.post(
            "/api/auth/password-reset/request/",
            {"email": account.email},
            format="json",
        )

    assert response.status_code == 200
    raw_token = response.json()["token"]
    reset_record = PasswordResetToken.objects.get(account=account)
    assert reset_record.status == PasswordResetStatus.PENDING
    assert fake_redis.ttls[services._password_reset_key(raw_token)] == 900

    response = api_client.post(
        "/api/auth/password-reset/confirm/",
        {"token": raw_token, "new_password": "new-password"},
        format="json",
    )

    assert response.status_code == 200
    reset_record.refresh_from_db()
    account.credential.refresh_from_db()
    assert reset_record.status == PasswordResetStatus.USED
    assert check_password("new-password", account.credential.password_hash)

    response = api_client.post(
        "/api/auth/password-reset/confirm/",
        {"token": raw_token, "new_password": "another-password"},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_password_reset_expired_redis_key_is_rejected(api_client, fake_redis):
    account = create_account("expired@example.com")

    with override_settings(AUTH_PASSWORD_RESET_DEBUG_RETURN_TOKEN=True):
        response = api_client.post(
            "/api/auth/password-reset/request/",
            {"email": account.email},
            format="json",
        )

    raw_token = response.json()["token"]
    fake_redis.delete(services._password_reset_key(raw_token))

    response = api_client.post(
        "/api/auth/password-reset/confirm/",
        {"token": raw_token, "new_password": "new-password"},
        format="json",
    )

    assert response.status_code == 400
    assert PasswordResetToken.objects.get(account=account).status == PasswordResetStatus.EXPIRED


@pytest.mark.django_db
def test_password_reset_confirm_rejects_weak_password(api_client):
    account = create_account("weak-reset@example.com")
    raw_token = "valid-reset-token"
    PasswordResetToken.objects.create(
        account=account,
        token_hash=services.hash_token(raw_token),
        expires_at=timezone.now() + timedelta(minutes=5),
    )

    response = api_client.post(
        "/api/auth/password-reset/confirm/",
        {"token": raw_token, "new_password": "short"},
        format="json",
    )

    assert response.status_code == 400
    assert "new_password" in response.json()
    assert PasswordResetToken.objects.get(account=account).status == PasswordResetStatus.PENDING


@pytest.mark.django_db
def test_password_reset_rate_limit_fails_closed_when_redis_is_unavailable(api_client, monkeypatch):
    class BrokenRedis:
        def incr(self, _key):
            raise redis.RedisError("redis unavailable")

    create_account("closed@example.com")
    monkeypatch.setattr(services, "_redis_client", lambda: BrokenRedis())

    response = api_client.post(
        "/api/auth/password-reset/request/",
        {"email": "closed@example.com"},
        format="json",
    )

    assert response.status_code == 429


@pytest.mark.django_db
def test_otp_uses_ttl_and_max_attempts(fake_redis):
    with override_settings(AUTH_OTP_TTL_SECONDS=120, AUTH_OTP_MAX_ATTEMPTS=2):
        services.issue_otp(purpose="login", subject="student@example.com", code="123456")
        otp_key = services._otp_key(purpose="login", subject="student@example.com")

        assert fake_redis.ttls[otp_key] == 120
        assert not services.verify_otp(
            purpose="login",
            subject="student@example.com",
            code="000000",
        )
        assert not services.verify_otp(
            purpose="login",
            subject="student@example.com",
            code="000001",
        )

    assert otp_key not in fake_redis.data


@pytest.mark.django_db
def test_expired_password_reset_row_is_marked_expired(api_client):
    account = create_account("row-expired@example.com")
    raw_token = "expired-token"
    PasswordResetToken.objects.create(
        account=account,
        token_hash=services.hash_token(raw_token),
        expires_at=timezone.now() - timedelta(seconds=1),
    )

    response = api_client.post(
        "/api/auth/password-reset/confirm/",
        {"token": raw_token, "new_password": "new-password"},
        format="json",
    )

    assert response.status_code == 400
    assert PasswordResetToken.objects.get(account=account).status == PasswordResetStatus.EXPIRED
