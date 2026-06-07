from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import jwt
import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.users import permissions
from apps.users.models import (
    Batch,
    BatchStatus,
    Department,
    DepartmentStatus,
    Institution,
    InstitutionStatus,
    StudentProfile,
    UserProfile,
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


def auth_headers(token: str) -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def allow_platform_admin(monkeypatch):
    monkeypatch.setattr(
        permissions,
        "remote_authorization_check",
        lambda **kwargs: kwargs["permission"] == "institution.manage",
    )


def allow_institution_admin(monkeypatch, institution_id):
    monkeypatch.setattr(
        permissions,
        "remote_authorization_check",
        lambda **kwargs: (
            kwargs["permission"] == "institution.manage"
            and kwargs["scope_type"] == "institution"
            and kwargs["scope_id"] == str(institution_id)
        ),
    )


def create_institution(code: str = "INST") -> Institution:
    return Institution.objects.create(name=f"{code} Institution", code=code)


@pytest.mark.django_db
def test_super_admin_can_manage_institutions(api_client, access_token, monkeypatch):
    allow_platform_admin(monkeypatch)

    response = api_client.post(
        "/api/users/institutions/",
        {"name": "Acme University", "code": " acme ", "settings": {"timezone": "UTC"}},
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 201
    institution_id = response.json()["id"]
    assert response.json()["code"] == "ACME"

    response = api_client.get(
        "/api/users/institutions/",
        {"q": "acme", "status": InstitutionStatus.ACTIVE, "sort": "-code", "page_size": "1"},
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1

    response = api_client.get(
        f"/api/users/institutions/{institution_id}/",
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Acme University"

    response = api_client.patch(
        f"/api/users/institutions/{institution_id}/",
        {"name": "Acme Learning", "code": "acu"},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Acme Learning"
    assert response.json()["code"] == "ACU"

    response = api_client.delete(
        f"/api/users/institutions/{institution_id}/",
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert response.json()["status"] == InstitutionStatus.ARCHIVED
    assert response.json()["deleted_at"] is not None
    assert Institution.objects.filter(id=institution_id).exists()

    response = api_client.get("/api/users/institutions/", **auth_headers(access_token))
    assert response.status_code == 200
    assert response.json()["count"] == 0


@pytest.mark.django_db
def test_non_super_admin_cannot_manage_institutions(api_client, access_token, monkeypatch):
    monkeypatch.setattr(permissions, "remote_authorization_check", lambda **_kwargs: False)

    response = api_client.post(
        "/api/users/institutions/",
        {"name": "Blocked University", "code": "BLOCK"},
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 403
    assert not Institution.objects.filter(code="BLOCK").exists()


@pytest.mark.django_db
def test_institution_admin_can_manage_own_departments_only(
    api_client,
    access_token,
    monkeypatch,
):
    institution = create_institution("OWN")
    other_institution = create_institution("OTHER")
    other_department = Department.objects.create(
        institution=other_institution,
        name="Other Department",
        code="OTHER-DEPT",
    )
    allow_institution_admin(monkeypatch, institution.id)

    response = api_client.post(
        "/api/users/departments/",
        {
            "institution_id": str(institution.id),
            "name": "Computer Science",
            "code": " cs ",
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201
    department_id = response.json()["id"]
    assert response.json()["code"] == "CS"

    response = api_client.get(
        "/api/users/departments/",
        {"institution_id": str(institution.id), "q": "computer", "page_size": "1"},
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1

    response = api_client.patch(
        f"/api/users/departments/{department_id}/",
        {"name": "Computer Engineering", "status": DepartmentStatus.INACTIVE},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["status"] == DepartmentStatus.INACTIVE

    response = api_client.get(
        f"/api/users/departments/{other_department.id}/",
        **auth_headers(access_token),
    )
    assert response.status_code == 403

    response = api_client.get(
        "/api/users/departments/",
        {"institution_id": str(other_institution.id)},
        **auth_headers(access_token),
    )
    assert response.status_code == 403

    response = api_client.get("/api/users/departments/", **auth_headers(access_token))
    assert response.status_code == 403

    response = api_client.delete(
        f"/api/users/departments/{department_id}/",
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert response.json()["status"] == DepartmentStatus.ARCHIVED

    department = Department.objects.get(id=department_id)
    assert department.deleted_at is not None


@pytest.mark.django_db
def test_department_soft_delete_preserves_profile_relationship(
    api_client,
    access_token,
    monkeypatch,
):
    institution = create_institution("REL")
    department = Department.objects.create(institution=institution, name="History", code="HIST")
    profile = UserProfile.objects.create(
        auth_account_id=uuid4(),
        institution=institution,
        first_name="Ada",
        last_name="Lovelace",
    )
    student = StudentProfile.objects.create(
        user_profile=profile,
        student_number="REL-1",
        department=department,
    )
    allow_institution_admin(monkeypatch, institution.id)

    response = api_client.delete(
        f"/api/users/departments/{department.id}/",
        **auth_headers(access_token),
    )

    assert response.status_code == 200
    student.refresh_from_db()
    assert student.department_id == department.id


@pytest.mark.django_db
def test_institution_admin_can_manage_batches_and_search(
    api_client,
    access_token,
    monkeypatch,
):
    institution = create_institution("BATCH")
    department = Department.objects.create(institution=institution, name="Science", code="SCI")
    other_institution = create_institution("OTHER")
    other_department = Department.objects.create(
        institution=other_institution,
        name="Other Science",
        code="OSCI",
    )
    allow_institution_admin(monkeypatch, institution.id)

    response = api_client.post(
        "/api/users/batches/",
        {
            "institution_id": str(institution.id),
            "department_id": str(other_department.id),
            "name": "Invalid Batch",
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 400

    response = api_client.post(
        "/api/users/batches/",
        {
            "institution_id": str(institution.id),
            "department_id": str(department.id),
            "name": "2026 Cohort",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201
    batch_id = response.json()["id"]

    response = api_client.get(
        "/api/users/batches/",
        {
            "institution_id": str(institution.id),
            "department_id": str(department.id),
            "q": "2026",
            "status": BatchStatus.ACTIVE,
            "sort": "name",
            "page_size": "1",
        },
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1

    response = api_client.patch(
        f"/api/users/batches/{batch_id}/",
        {"start_date": "2026-12-31", "end_date": "2026-01-01"},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 400

    response = api_client.patch(
        f"/api/users/batches/{batch_id}/",
        {"status": BatchStatus.COMPLETED, "department_id": None},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["status"] == BatchStatus.COMPLETED
    assert response.json()["department_id"] is None

    response = api_client.delete(f"/api/users/batches/{batch_id}/", **auth_headers(access_token))
    assert response.status_code == 200
    assert response.json()["status"] == BatchStatus.ARCHIVED

    response = api_client.get(
        "/api/users/batches/",
        {"institution_id": str(institution.id)},
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert response.json()["count"] == 0


@pytest.mark.django_db
def test_batch_soft_delete_preserves_profile_relationship(api_client, access_token, monkeypatch):
    institution = create_institution("BREL")
    batch = Batch.objects.create(institution=institution, name="2026")
    profile = UserProfile.objects.create(
        auth_account_id=uuid4(),
        institution=institution,
        first_name="Grace",
        last_name="Hopper",
    )
    student = StudentProfile.objects.create(
        user_profile=profile,
        student_number="BREL-1",
        batch=batch,
    )
    allow_institution_admin(monkeypatch, institution.id)

    response = api_client.delete(f"/api/users/batches/{batch.id}/", **auth_headers(access_token))

    assert response.status_code == 200
    student.refresh_from_db()
    assert student.batch_id == batch.id


@pytest.mark.django_db
def test_auth_service_denial_denies_organization_access(api_client, access_token, monkeypatch):
    institution = create_institution("DENY")
    monkeypatch.setattr(permissions, "remote_authorization_check", lambda **_kwargs: False)

    response = api_client.get(
        "/api/users/departments/",
        {"institution_id": str(institution.id)},
        **auth_headers(access_token),
    )

    assert response.status_code == 403
