from __future__ import annotations

from uuid import uuid4

import pytest
from django.contrib.auth.hashers import make_password
from django.test import override_settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIClient

from apps.authentication import services
from apps.authentication.models import Account, AccountStatus, Credential, ExternalIdentity


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def oidc_settings():
    with override_settings(
        AUTH_OIDC_ENABLED=True,
        AUTH_OIDC_PROVIDER_LABEL="Campus SSO",
        AUTH_OIDC_ISSUER_URL="https://idp.example.test",
        AUTH_OIDC_CLIENT_ID="learngrid-web",
        AUTH_OIDC_CLIENT_SECRET="secret",
        AUTH_OIDC_REDIRECT_URI="http://localhost:5173/auth/oidc/callback",
        AUTH_OIDC_SCOPES="openid email profile",
        AUTH_OIDC_REQUIRE_EMAIL_VERIFIED=True,
    ):
        yield


def create_active_account(email="student@example.com") -> Account:
    account = Account.objects.create(email=email, status=AccountStatus.ACTIVE)
    Credential.objects.create(account=account, password_hash=make_password("correct-password"))
    return account


def discovery_payload() -> dict[str, str]:
    return {
        "authorization_endpoint": "https://idp.example.test/oauth2/authorize",
        "token_endpoint": "https://idp.example.test/oauth2/token",
        "jwks_uri": "https://idp.example.test/oauth2/jwks",
    }


def oidc_claims(email="student@example.com", *, email_verified=True, subject=None):
    return {
        "iss": "https://idp.example.test",
        "sub": subject or str(uuid4()),
        "email": email,
        "email_verified": email_verified,
        "nonce": "nonce-is-checked-by-service-test-double",
        "name": "Student Example",
    }


def start_authorization(api_client, monkeypatch):
    monkeypatch.setattr(services, "_oidc_discovery", discovery_payload)
    response = api_client.post("/api/auth/oidc/authorize/", {}, format="json")
    assert response.status_code == 200
    return response.json()["state"]


@pytest.mark.django_db
def test_oidc_config_reports_disabled_by_default(api_client):
    response = api_client.get("/api/auth/oidc/config/")

    assert response.status_code == 200
    assert response.json()["enabled"] is False


@pytest.mark.django_db
def test_oidc_authorize_generates_provider_url(api_client, oidc_settings, monkeypatch, fake_redis):
    monkeypatch.setattr(services, "_oidc_discovery", discovery_payload)
    response = api_client.post("/api/auth/oidc/authorize/", {}, format="json")

    assert response.status_code == 200
    body = response.json()
    assert body["authorization_url"].startswith("https://idp.example.test/oauth2/authorize?")
    assert "code_challenge_method=S256" in body["authorization_url"]
    assert body["state"]
    assert body["state"] in body["authorization_url"]
    assert len(fake_redis.data) == 1


@pytest.mark.django_db
def test_oidc_callback_matches_existing_account_and_issues_tokens(
    api_client,
    oidc_settings,
    monkeypatch,
):
    account = create_active_account()
    subject = str(uuid4())
    state = start_authorization(api_client, monkeypatch)
    monkeypatch.setattr(services, "_exchange_oidc_code", lambda **_kwargs: {"id_token": "id-token"})
    monkeypatch.setattr(
        services,
        "_validate_oidc_id_token",
        lambda *_args, **_kwargs: oidc_claims(subject=subject),
    )

    response = api_client.post(
        "/api/auth/oidc/callback/",
        {"code": "provider-code", "state": state},
        format="json",
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access", "refresh", "access_expires_at", "refresh_expires_at"}
    identity = ExternalIdentity.objects.get(issuer="https://idp.example.test", subject=subject)
    assert identity.account == account
    assert identity.email == "student@example.com"


@pytest.mark.django_db
def test_oidc_callback_reuses_existing_identity_idempotently(
    api_client,
    oidc_settings,
    monkeypatch,
):
    create_active_account()
    subject = str(uuid4())
    monkeypatch.setattr(services, "_exchange_oidc_code", lambda **_kwargs: {"id_token": "id-token"})
    monkeypatch.setattr(
        services,
        "_validate_oidc_id_token",
        lambda *_args, **_kwargs: oidc_claims(subject=subject),
    )

    first_state = start_authorization(api_client, monkeypatch)
    second_state = start_authorization(api_client, monkeypatch)
    first_response = api_client.post(
        "/api/auth/oidc/callback/",
        {"code": "provider-code", "state": first_state},
        format="json",
    )
    second_response = api_client.post(
        "/api/auth/oidc/callback/",
        {"code": "provider-code", "state": second_state},
        format="json",
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert ExternalIdentity.objects.filter(subject=subject).count() == 1


@pytest.mark.django_db
def test_oidc_callback_rejects_unverified_email(api_client, oidc_settings, monkeypatch):
    create_active_account()
    state = start_authorization(api_client, monkeypatch)
    monkeypatch.setattr(services, "_exchange_oidc_code", lambda **_kwargs: {"id_token": "id-token"})
    monkeypatch.setattr(
        services,
        "_validate_oidc_id_token",
        lambda *_args, **_kwargs: oidc_claims(email_verified=False),
    )

    response = api_client.post(
        "/api/auth/oidc/callback/",
        {"code": "provider-code", "state": state},
        format="json",
    )

    assert response.status_code == 403
    assert ExternalIdentity.objects.count() == 0


@pytest.mark.django_db
def test_oidc_callback_rejects_unknown_or_inactive_account(
    api_client,
    oidc_settings,
    monkeypatch,
):
    Account.objects.create(email="disabled@example.com", status=AccountStatus.DEACTIVATED)
    monkeypatch.setattr(services, "_exchange_oidc_code", lambda **_kwargs: {"id_token": "id-token"})
    monkeypatch.setattr(
        services,
        "_validate_oidc_id_token",
        lambda *_args, **_kwargs: oidc_claims(email="missing@example.com"),
    )
    missing_state = start_authorization(api_client, monkeypatch)

    missing_response = api_client.post(
        "/api/auth/oidc/callback/",
        {"code": "provider-code", "state": missing_state},
        format="json",
    )

    monkeypatch.setattr(
        services,
        "_validate_oidc_id_token",
        lambda *_args, **_kwargs: oidc_claims(email="disabled@example.com"),
    )
    disabled_state = start_authorization(api_client, monkeypatch)
    disabled_response = api_client.post(
        "/api/auth/oidc/callback/",
        {"code": "provider-code", "state": disabled_state},
        format="json",
    )

    assert missing_response.status_code == 403
    assert disabled_response.status_code == 403
    assert ExternalIdentity.objects.count() == 0


@pytest.mark.django_db
def test_oidc_callback_rejects_reused_state(api_client, oidc_settings, monkeypatch):
    create_active_account()
    state = start_authorization(api_client, monkeypatch)
    monkeypatch.setattr(services, "_exchange_oidc_code", lambda **_kwargs: {"id_token": "id-token"})
    monkeypatch.setattr(
        services, "_validate_oidc_id_token", lambda *_args, **_kwargs: oidc_claims()
    )

    first_response = api_client.post(
        "/api/auth/oidc/callback/",
        {"code": "provider-code", "state": state},
        format="json",
    )
    second_response = api_client.post(
        "/api/auth/oidc/callback/",
        {"code": "provider-code", "state": state},
        format="json",
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 403


@pytest.mark.django_db
def test_oidc_callback_handles_provider_failure(api_client, oidc_settings, monkeypatch):
    create_active_account()
    state = start_authorization(api_client, monkeypatch)

    def fail_exchange(**_kwargs):
        raise AuthenticationFailed("OIDC provider rejected the authorization code.")

    monkeypatch.setattr(services, "_exchange_oidc_code", fail_exchange)

    response = api_client.post(
        "/api/auth/oidc/callback/",
        {"code": "provider-code", "state": state},
        format="json",
    )

    assert response.status_code == 403
