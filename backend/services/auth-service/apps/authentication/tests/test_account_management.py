from uuid import uuid4

import pytest
from django.contrib.auth.hashers import check_password, make_password
from rest_framework.test import APIClient

from apps.authentication import services
from apps.authentication.models import (
    Account,
    AccountStatus,
    AssignmentScopeType,
    AuthorizationAuditLog,
    Credential,
    RefreshToken,
    Role,
    RoleAssignment,
)


@pytest.fixture
def api_client():
    return APIClient()


def create_account(email: str) -> Account:
    account = Account.objects.create(email=email, status=AccountStatus.ACTIVE)
    Credential.objects.create(account=account, password_hash=make_password("correct-password"))
    return account


def issue_access_token(account: Account) -> str:
    return services.issue_token_pair(account).access


def make_super_admin(email: str = "profile-admin@example.com") -> Account:
    account = create_account(email)
    services.assign_role(
        account=account,
        role=Role.objects.get(code="super_admin"),
        scope_type=AssignmentScopeType.PLATFORM,
    )
    return account


@pytest.mark.django_db
def test_admin_can_create_account_with_temporary_password_and_role(api_client):
    admin = make_super_admin()
    access = issue_access_token(admin)
    institution_id = uuid4()

    response = api_client.post(
        "/api/auth/accounts/",
        {
            "email": "student@example.com",
            "phone": "+15550000001",
            "temporary_password": "temporary-pass",
            "role_code": "student",
            "scope_type": "institution",
            "scope_id": str(institution_id),
        },
        HTTP_AUTHORIZATION=f"Bearer {access}",
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert "temporary_password" not in body
    assert "password_hash" not in body
    assert body["email"] == "student@example.com"
    assert body["must_change_password"] is True

    account = Account.objects.get(email="student@example.com")
    assert account.status == AccountStatus.ACTIVE
    assert check_password("temporary-pass", account.credential.password_hash)
    assert RoleAssignment.objects.filter(
        account=account,
        role__code="student",
        scope_type=AssignmentScopeType.INSTITUTION,
        scope_id=institution_id,
        revoked_at__isnull=True,
    ).exists()
    assert AuthorizationAuditLog.objects.filter(
        actor_account=admin,
        target_account=account,
        event_type=services.AUTH_ACCOUNT_CREATED_AUDIT_EVENT,
        scope_type=AssignmentScopeType.INSTITUTION,
        scope_id=institution_id,
    ).exists()


@pytest.mark.django_db
def test_account_creation_rejects_weak_password(api_client):
    admin = make_super_admin()
    access = issue_access_token(admin)

    response = api_client.post(
        "/api/auth/accounts/",
        {
            "email": "weak@example.com",
            "temporary_password": "short",
            "scope_type": "platform",
        },
        HTTP_AUTHORIZATION=f"Bearer {access}",
        format="json",
    )

    assert response.status_code == 400
    assert "temporary_password" in response.json()
    assert not Account.objects.filter(email="weak@example.com").exists()


@pytest.mark.django_db
def test_unauthorized_account_creation_is_denied(api_client):
    actor = create_account("regular@example.com")
    access = issue_access_token(actor)

    response = api_client.post(
        "/api/auth/accounts/",
        {"email": "blocked@example.com", "temporary_password": "temporary-pass"},
        HTTP_AUTHORIZATION=f"Bearer {access}",
        format="json",
    )

    assert response.status_code == 403
    assert not Account.objects.filter(email="blocked@example.com").exists()


@pytest.mark.django_db
def test_account_update_changes_email_and_phone_without_password_data(api_client):
    admin = make_super_admin()
    target = create_account("old@example.com")
    access = issue_access_token(admin)

    response = api_client.patch(
        f"/api/auth/accounts/{target.id}/",
        {
            "email": "new@example.com",
            "phone": "+15550000002",
            "scope_type": "platform",
        },
        HTTP_AUTHORIZATION=f"Bearer {access}",
        format="json",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["phone"] == "+15550000002"
    assert "password_hash" not in body
    target.refresh_from_db()
    assert target.email == "new@example.com"
    assert target.phone == "+15550000002"
    assert AuthorizationAuditLog.objects.filter(
        actor_account=admin,
        target_account=target,
        event_type=services.AUTH_ACCOUNT_UPDATED_AUDIT_EVENT,
        scope_type=AssignmentScopeType.PLATFORM,
    ).exists()


@pytest.mark.django_db
def test_deactivation_changes_status_and_invalidates_tokens(api_client):
    admin = make_super_admin()
    target = create_account("deactivate-me@example.com")
    target_tokens = services.issue_token_pair(target)
    access = issue_access_token(admin)

    response = api_client.post(
        f"/api/auth/accounts/{target.id}/deactivate/",
        {"scope_type": "platform"},
        HTTP_AUTHORIZATION=f"Bearer {access}",
        format="json",
    )

    assert response.status_code == 200
    target.refresh_from_db()
    assert target.status == AccountStatus.DEACTIVATED
    assert target.deleted_at is not None
    assert RefreshToken.objects.get(
        token_hash=services.hash_token(target_tokens.refresh)
    ).revoked_at
    assert AuthorizationAuditLog.objects.filter(
        actor_account=admin,
        target_account=target,
        event_type=services.AUTH_ACCOUNT_DEACTIVATED_AUDIT_EVENT,
        scope_type=AssignmentScopeType.PLATFORM,
    ).exists()

    response = api_client.get(
        "/api/auth/session/",
        HTTP_AUTHORIZATION=f"Bearer {target_tokens.access}",
    )
    assert response.status_code == 403
