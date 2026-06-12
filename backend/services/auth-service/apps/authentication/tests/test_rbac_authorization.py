from uuid import uuid4

import pytest
import redis
from django.contrib.auth.hashers import make_password
from rest_framework.test import APIClient

from apps.authentication import services
from apps.authentication.models import (
    Account,
    AccountStatus,
    AssignmentScopeType,
    AuthorizationAuditEvent,
    AuthorizationAuditLog,
    Credential,
    Permission,
    Role,
    RolePermission,
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


@pytest.mark.django_db
def test_seeded_roles_and_permissions_exist():
    expected_roles = {
        "super_admin",
        "institution_admin",
        "instructor",
        "teaching_assistant",
        "student",
        "parent_guardian",
    }
    expected_permissions = {
        "rbac.manage",
        "institution.manage",
        "profile.view",
        "profile.manage",
        "course.view",
        "course.manage",
        "content.view",
        "content.manage",
        "enrollment.view",
        "enrollment.manage",
        "progress.view",
        "progress.manage",
        "assessment.view",
        "assessment.manage",
        "submission.view",
        "submission.manage",
        "grade.view",
        "grade.manage",
        "notification.view",
        "notification.manage",
        "analytics.view",
    }

    assert expected_roles <= set(Role.objects.values_list("code", flat=True))
    assert expected_permissions <= set(Permission.objects.values_list("code", flat=True))
    assert (
        RolePermission.objects.filter(role__code="super_admin").count()
        == Permission.objects.count()
    )


@pytest.mark.django_db
def test_scoped_permission_checks_allow_exact_scope_and_deny_other_scope():
    account = create_account("instructor@example.com")
    course_id = uuid4()
    other_course_id = uuid4()
    instructor_role = Role.objects.get(code="instructor")
    services.assign_role(
        account=account,
        role=instructor_role,
        scope_type=AssignmentScopeType.COURSE,
        scope_id=course_id,
    )

    assert services.has_permission(
        account,
        "course.manage",
        scope_type=AssignmentScopeType.COURSE,
        scope_id=course_id,
    )
    assert not services.has_permission(
        account,
        "course.manage",
        scope_type=AssignmentScopeType.COURSE,
        scope_id=other_course_id,
    )
    assert not services.has_permission(account, "course.manage")


@pytest.mark.django_db
def test_super_admin_can_perform_platform_wide_actions():
    account = create_account("super-admin@example.com")
    services.assign_role(
        account=account,
        role=Role.objects.get(code="super_admin"),
        scope_type=AssignmentScopeType.PLATFORM,
    )

    assert services.has_permission(account, "rbac.manage")
    assert services.has_permission(
        account,
        "grade.manage",
        scope_type=AssignmentScopeType.COURSE,
        scope_id=uuid4(),
    )


@pytest.mark.django_db
def test_assessment_scope_is_enforced_for_object_authorization():
    account = create_account("ta@example.com")
    assessment_id = uuid4()
    services.assign_role(
        account=account,
        role=Role.objects.get(code="teaching_assistant"),
        scope_type=AssignmentScopeType.ASSESSMENT,
        scope_id=assessment_id,
    )

    assert services.has_permission(
        account,
        "submission.manage",
        scope_type=AssignmentScopeType.ASSESSMENT,
        scope_id=assessment_id,
    )
    assert not services.has_permission(
        account,
        "submission.manage",
        scope_type=AssignmentScopeType.ASSESSMENT,
        scope_id=uuid4(),
    )


@pytest.mark.django_db
def test_role_assignment_create_and_revoke_write_audit_logs():
    actor = create_account("actor@example.com")
    target = create_account("target@example.com")
    assignment = services.assign_role(
        account=target,
        role=Role.objects.get(code="student"),
        scope_type=AssignmentScopeType.COURSE,
        scope_id=uuid4(),
        assigned_by_account=actor,
    )

    services.revoke_role_assignment(assignment, revoked_by_account=actor)

    assert AuthorizationAuditLog.objects.filter(
        event_type=AuthorizationAuditEvent.ROLE_ASSIGNMENT_CREATED,
        actor_account=actor,
        target_account=target,
    ).exists()
    assert AuthorizationAuditLog.objects.filter(
        event_type=AuthorizationAuditEvent.ROLE_ASSIGNMENT_REVOKED,
        actor_account=actor,
        target_account=target,
    ).exists()


@pytest.mark.django_db
def test_permission_cache_is_used_and_invalidated(monkeypatch):
    account = create_account("cached@example.com")
    course_id = uuid4()
    cache = {}

    class FakeRedis:
        def get(self, key):
            return cache.get(key)

        def setex(self, key, _ttl, value):
            cache[key] = value

        def scan_iter(self, pattern):
            prefix = pattern.removesuffix("*")
            return [key for key in cache if key.startswith(prefix)]

        def delete(self, *keys):
            for key in keys:
                cache.pop(key, None)

    monkeypatch.setattr(services, "_redis_client", lambda: FakeRedis())
    assignment = services.assign_role(
        account=account,
        role=Role.objects.get(code="instructor"),
        scope_type=AssignmentScopeType.COURSE,
        scope_id=course_id,
    )

    assert services.has_permission(
        account,
        "course.manage",
        scope_type=AssignmentScopeType.COURSE,
        scope_id=course_id,
    )
    assert cache

    RolePermission.objects.filter(role=assignment.role, permission__code="course.manage").delete()
    assert services.has_permission(
        account,
        "course.manage",
        scope_type=AssignmentScopeType.COURSE,
        scope_id=course_id,
    )

    services.revoke_role_assignment(assignment)
    assert not cache


@pytest.mark.django_db
def test_permission_check_falls_back_to_database_when_redis_fails(monkeypatch):
    account = create_account("fallback@example.com")
    course_id = uuid4()

    class BrokenRedis:
        def get(self, _key):
            raise redis.RedisError("redis unavailable")

        def scan_iter(self, _pattern):
            raise redis.RedisError("redis unavailable")

    monkeypatch.setattr(services, "_redis_client", lambda: BrokenRedis())
    services.assign_role(
        account=account,
        role=Role.objects.get(code="instructor"),
        scope_type=AssignmentScopeType.COURSE,
        scope_id=course_id,
    )

    assert services.has_permission(
        account,
        "course.manage",
        scope_type=AssignmentScopeType.COURSE,
        scope_id=course_id,
    )


@pytest.mark.django_db
def test_authorization_check_endpoint_returns_allowed_without_object_leak(api_client):
    account = create_account("api-instructor@example.com")
    course_id = uuid4()
    services.assign_role(
        account=account,
        role=Role.objects.get(code="instructor"),
        scope_type=AssignmentScopeType.COURSE,
        scope_id=course_id,
    )
    access = issue_access_token(account)

    response = api_client.post(
        "/api/auth/authorization/check/",
        {"permission": "course.manage", "scope_type": "course", "scope_id": str(course_id)},
        HTTP_AUTHORIZATION=f"Bearer {access}",
        format="json",
    )
    assert response.status_code == 200
    assert response.json() == {"allowed": True}

    response = api_client.post(
        "/api/auth/authorization/check/",
        {"permission": "course.manage", "scope_type": "course", "scope_id": str(uuid4())},
        HTTP_AUTHORIZATION=f"Bearer {access}",
        format="json",
    )
    assert response.status_code == 200
    assert response.json() == {"allowed": False}


@pytest.mark.django_db
def test_rbac_assignment_api_requires_management_and_records_audit(api_client):
    admin = create_account("rbac-admin@example.com")
    target = create_account("rbac-target@example.com")
    course_id = uuid4()
    services.assign_role(
        account=admin,
        role=Role.objects.get(code="super_admin"),
        scope_type=AssignmentScopeType.PLATFORM,
    )
    access = issue_access_token(admin)

    response = api_client.post(
        "/api/auth/rbac/role-assignments/",
        {
            "account_id": str(target.id),
            "role_code": "student",
            "scope_type": "course",
            "scope_id": str(course_id),
        },
        HTTP_AUTHORIZATION=f"Bearer {access}",
        format="json",
    )

    assert response.status_code == 201
    assignment_id = response.json()["id"]
    assert AuthorizationAuditLog.objects.filter(
        event_type=AuthorizationAuditEvent.ROLE_ASSIGNMENT_CREATED,
        target_account=target,
    ).exists()

    response = api_client.delete(
        f"/api/auth/rbac/role-assignments/{assignment_id}/",
        HTTP_AUTHORIZATION=f"Bearer {access}",
    )
    assert response.status_code == 200
    assert response.json() == {"status": "revoked"}
    assert AuthorizationAuditLog.objects.filter(
        event_type=AuthorizationAuditEvent.ROLE_ASSIGNMENT_REVOKED,
        target_account=target,
    ).exists()
