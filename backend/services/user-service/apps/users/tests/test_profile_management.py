from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import jwt
import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.users import permissions, services
from apps.users.models import (
    AdminProfile,
    AdminType,
    Batch,
    Department,
    Institution,
    InstructorProfile,
    StudentProfile,
    UserProfile,
    UserProfileStatus,
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
    monkeypatch.setattr(permissions, "remote_authorization_check", lambda **_kwargs: True)


@pytest.fixture
def auth_account_mock(monkeypatch):
    calls = []

    def create_auth_account(**kwargs):
        calls.append(kwargs)
        return {"id": str(uuid4()), "email": kwargs["email"], "status": "active"}

    monkeypatch.setattr(services, "create_auth_account", create_auth_account)
    return calls


def auth_headers(token: str) -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def token_for_account(account_id) -> str:
    now = timezone.now()
    return jwt.encode(
        {
            "iss": settings.AUTH_JWT_ISSUER,
            "sub": str(account_id),
            "typ": "access",
            "jti": str(uuid4()),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
        settings.AUTH_JWT_SIGNING_KEY,
        algorithm=settings.AUTH_JWT_ALGORITHM,
    )


def create_institution(code: str = "INST") -> Institution:
    return Institution.objects.create(name=f"{code} Institution", code=code)


def create_student_profile(
    *,
    institution: Institution,
    first_name: str = "Ada",
    last_name: str = "Lovelace",
    student_number: str = "STU-1",
    batch: Batch | None = None,
    department: Department | None = None,
) -> UserProfile:
    profile = UserProfile.objects.create(
        auth_account_id=uuid4(),
        institution=institution,
        first_name=first_name,
        last_name=last_name,
    )
    StudentProfile.objects.create(
        user_profile=profile,
        student_number=student_number,
        batch=batch,
        department=department,
    )
    return profile


@pytest.mark.django_db
def test_create_student_instructor_and_admin_profiles(api_client, access_token, auth_account_mock):
    institution = create_institution()
    department = Department.objects.create(institution=institution, name="Engineering", code="ENG")
    batch = Batch.objects.create(institution=institution, department=department, name="2026")

    responses = []
    responses.append(
        api_client.post(
            "/api/users/profiles/",
            {
                "email": "student@example.com",
                "temporary_password": "temporary-pass",
                "profile_type": "student",
                "institution_id": str(institution.id),
                "first_name": "Ada",
                "last_name": "Lovelace",
                "student": {
                    "student_number": "STU-100",
                    "batch_id": str(batch.id),
                    "department_id": str(department.id),
                },
            },
            **auth_headers(access_token),
            format="json",
        )
    )
    responses.append(
        api_client.post(
            "/api/users/profiles/",
            {
                "email": "instructor@example.com",
                "temporary_password": "temporary-pass",
                "profile_type": "instructor",
                "institution_id": str(institution.id),
                "first_name": "Grace",
                "last_name": "Hopper",
                "instructor": {"employee_number": "EMP-100", "department_id": str(department.id)},
            },
            **auth_headers(access_token),
            format="json",
        )
    )
    responses.append(
        api_client.post(
            "/api/users/profiles/",
            {
                "email": "admin@example.com",
                "temporary_password": "temporary-pass",
                "profile_type": "admin",
                "institution_id": str(institution.id),
                "first_name": "Mary",
                "last_name": "Jackson",
                "admin": {"admin_type": AdminType.INSTITUTION_ADMIN},
            },
            **auth_headers(access_token),
            format="json",
        )
    )

    assert [response.status_code for response in responses] == [201, 201, 201]
    assert {response.json()["profile_type"] for response in responses} == {
        "student",
        "instructor",
        "admin",
    }
    assert UserProfile.objects.count() == 3
    assert StudentProfile.objects.filter(student_number="STU-100").exists()
    assert InstructorProfile.objects.filter(employee_number="EMP-100").exists()
    assert AdminProfile.objects.filter(admin_type=AdminType.INSTITUTION_ADMIN).exists()
    assert [call["role_code"] for call in auth_account_mock] == [
        "student",
        "instructor",
        "institution_admin",
    ]


@pytest.mark.django_db
def test_update_profile_and_optional_auth_account_fields(api_client, access_token, monkeypatch):
    institution = create_institution()
    profile = create_student_profile(institution=institution)
    auth_updates = []

    def update_auth_account(**kwargs):
        auth_updates.append(kwargs)
        return {"status": "active"}

    monkeypatch.setattr(services, "update_auth_account", update_auth_account)

    response = api_client.patch(
        f"/api/users/profiles/{profile.id}/",
        {
            "email": "updated@example.com",
            "phone": "+15550000001",
            "first_name": "Ada Updated",
            "student": {"student_number": "STU-2"},
        },
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] == "Ada Updated"
    assert body["role_profile"]["student_number"] == "STU-2"
    assert auth_updates[0]["email"] == "updated@example.com"
    assert auth_updates[0]["phone"] == "+15550000001"


@pytest.mark.django_db
def test_deactivate_profile_and_auth_account_together(api_client, access_token, monkeypatch):
    institution = create_institution()
    profile = create_student_profile(institution=institution)
    deactivations = []

    def deactivate_auth_account(**kwargs):
        deactivations.append(kwargs)
        return {"status": "deactivated"}

    monkeypatch.setattr(services, "deactivate_auth_account", deactivate_auth_account)

    response = api_client.post(
        f"/api/users/profiles/{profile.id}/deactivate/",
        **auth_headers(access_token),
    )

    assert response.status_code == 200
    profile.refresh_from_db()
    assert profile.status == UserProfileStatus.DEACTIVATED
    assert profile.deleted_at is not None
    assert deactivations[0]["auth_account_id"] == profile.auth_account_id


@pytest.mark.django_db
def test_search_supports_pagination_filtering_sorting_and_institution_scope(
    api_client,
    access_token,
    monkeypatch,
):
    institution = create_institution("A")
    other_institution = create_institution("B")
    department = Department.objects.create(institution=institution, name="Science", code="SCI")
    batch = Batch.objects.create(institution=institution, department=department, name="2026")
    create_student_profile(
        institution=institution,
        first_name="Ada",
        last_name="Lovelace",
        student_number="STU-A",
        batch=batch,
        department=department,
    )
    create_student_profile(
        institution=other_institution,
        first_name="Alan",
        last_name="Turing",
        student_number="STU-B",
    )
    checks = []

    def remote_authorization_check(**kwargs):
        checks.append(kwargs)
        return kwargs["scope_id"] == str(institution.id)

    monkeypatch.setattr(permissions, "remote_authorization_check", remote_authorization_check)

    response = api_client.get(
        "/api/users/profiles/",
        {
            "institution_id": str(institution.id),
            "profile_type": "student",
            "department_id": str(department.id),
            "batch_id": str(batch.id),
            "q": "Ada",
            "sort": "first_name",
            "page_size": "1",
        },
        **auth_headers(access_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["results"][0]["first_name"] == "Ada"
    assert checks[0]["permission"] == "profile.view"
    assert checks[0]["scope_type"] == "institution"
    assert checks[0]["scope_id"] == str(institution.id)


@pytest.mark.django_db
def test_institution_admin_cannot_access_another_institution_profile(
    api_client,
    access_token,
    monkeypatch,
):
    institution = create_institution("A")
    other_institution = create_institution("B")
    profile = create_student_profile(institution=other_institution)

    monkeypatch.setattr(
        permissions,
        "remote_authorization_check",
        lambda **kwargs: kwargs["scope_id"] == str(institution.id),
    )

    response = api_client.get(
        f"/api/users/profiles/{profile.id}/",
        **auth_headers(access_token),
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_bulk_import_placeholder_returns_501(api_client, access_token):
    institution = create_institution()

    response = api_client.post(
        "/api/users/import-jobs/",
        {"institution_id": str(institution.id)},
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 501
    assert response.json()["code"] == "not_implemented"


@pytest.mark.django_db
def test_auth_service_failure_during_create_returns_controlled_error(
    api_client,
    access_token,
    monkeypatch,
):
    institution = create_institution()

    def create_auth_account(**_kwargs):
        raise services.AuthServiceError("Auth-service is unavailable.")

    monkeypatch.setattr(services, "create_auth_account", create_auth_account)

    response = api_client.post(
        "/api/users/profiles/",
        {
            "email": "failure@example.com",
            "temporary_password": "temporary-pass",
            "profile_type": "student",
            "institution_id": str(institution.id),
            "first_name": "Failed",
            "last_name": "User",
            "student": {"student_number": "STU-F"},
        },
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Auth-service is unavailable."


@pytest.mark.django_db
def test_local_create_failure_after_auth_account_creation_triggers_compensation(
    api_client,
    access_token,
    monkeypatch,
):
    institution = create_institution()
    create_student_profile(institution=institution, student_number="STU-DUP")
    auth_account_id = uuid4()
    deactivations = []

    monkeypatch.setattr(
        services,
        "create_auth_account",
        lambda **kwargs: {"id": str(auth_account_id), "email": kwargs["email"]},
    )

    def deactivate_auth_account(**kwargs):
        deactivations.append(kwargs)
        return {"status": "deactivated"}

    monkeypatch.setattr(services, "deactivate_auth_account", deactivate_auth_account)

    response = api_client.post(
        "/api/users/profiles/",
        {
            "email": "duplicate@example.com",
            "temporary_password": "temporary-pass",
            "profile_type": "student",
            "institution_id": str(institution.id),
            "first_name": "Duplicate",
            "last_name": "Student",
            "student": {"student_number": "STU-DUP"},
        },
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 400
    assert deactivations[0]["auth_account_id"] == str(auth_account_id)


@pytest.mark.django_db
def test_current_profile_returns_authenticated_profile(api_client):
    institution = create_institution()
    account_id = uuid4()
    profile = UserProfile.objects.create(
        auth_account_id=account_id,
        institution=institution,
        first_name="Current",
        last_name="Student",
    )
    StudentProfile.objects.create(user_profile=profile, student_number="STU-ME")

    response = api_client.get(
        "/api/users/profiles/me/",
        **auth_headers(token_for_account(account_id)),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(profile.id)
    assert body["auth_account_id"] == str(account_id)
    assert body["profile_type"] == "student"


@pytest.mark.django_db
def test_current_profile_rejects_missing_profile(api_client):
    response = api_client.get(
        "/api/users/profiles/me/",
        **auth_headers(token_for_account(uuid4())),
    )

    assert response.status_code == 404
