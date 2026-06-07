from __future__ import annotations

import json
from typing import Any
from urllib import error, request as urlrequest

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from .models import (
    AdminProfile,
    AdminType,
    Batch,
    BatchStatus,
    Department,
    DepartmentStatus,
    Institution,
    InstitutionStatus,
    InstructorProfile,
    StudentProfile,
    UserProfile,
    UserProfileStatus,
)


class AuthServiceError(APIException):
    status_code = 502
    default_code = "auth_service_error"
    default_detail = "Auth-service request failed."


def _auth_service_request(
    *,
    token: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = json.dumps(payload or {}).encode("utf-8")
    request = urlrequest.Request(
        f"{settings.AUTH_SERVICE_BASE_URL.rstrip('/')}{path}",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urlrequest.urlopen(request, timeout=3) as response:
            if response.status >= 400:
                raise AuthServiceError()
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise AuthServiceError(f"Auth-service returned HTTP {exc.code}.") from exc
    except (error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise AuthServiceError("Auth-service is unavailable.") from exc


def create_auth_account(
    *,
    token: str,
    email: str,
    phone: str | None,
    temporary_password: str,
    role_code: str,
    scope_type: str,
    scope_id,
) -> dict[str, Any]:
    return _auth_service_request(
        token=token,
        method="POST",
        path="/api/auth/accounts/",
        payload={
            "email": email,
            "phone": phone,
            "temporary_password": temporary_password,
            "role_code": role_code,
            "scope_type": scope_type,
            "scope_id": str(scope_id) if scope_id else None,
        },
    )


def update_auth_account(
    *,
    token: str,
    auth_account_id,
    scope_type: str,
    scope_id,
    email: str | None = None,
    phone: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    payload = {
        "scope_type": scope_type,
        "scope_id": str(scope_id) if scope_id else None,
    }
    if email is not None:
        payload["email"] = email
    if phone is not None:
        payload["phone"] = phone
    if status is not None:
        payload["status"] = status
    return _auth_service_request(
        token=token,
        method="PATCH",
        path=f"/api/auth/accounts/{auth_account_id}/",
        payload=payload,
    )


def deactivate_auth_account(*, token: str, auth_account_id, scope_type: str, scope_id) -> dict[str, Any]:
    return _auth_service_request(
        token=token,
        method="POST",
        path=f"/api/auth/accounts/{auth_account_id}/deactivate/",
        payload={"scope_type": scope_type, "scope_id": str(scope_id) if scope_id else None},
    )


def _scope_for_institution(institution_id) -> tuple[str, object | None]:
    if institution_id:
        return "institution", institution_id
    return "platform", None


def _get_institution(institution_id):
    if not institution_id:
        return None
    try:
        return Institution.objects.get(id=institution_id, deleted_at__isnull=True)
    except Institution.DoesNotExist as exc:
        raise ValidationError({"institution_id": "Institution was not found."}) from exc


def _get_department(department_id, institution: Institution | None):
    if not department_id:
        return None
    try:
        department = Department.objects.get(id=department_id, deleted_at__isnull=True)
    except Department.DoesNotExist as exc:
        raise ValidationError({"department_id": "Department was not found."}) from exc
    if institution and department.institution_id != institution.id:
        raise ValidationError({"department_id": "Department does not belong to the profile institution."})
    return department


def _get_batch(batch_id, institution: Institution | None):
    if not batch_id:
        return None
    try:
        batch = Batch.objects.get(id=batch_id, deleted_at__isnull=True)
    except Batch.DoesNotExist as exc:
        raise ValidationError({"batch_id": "Batch was not found."}) from exc
    if institution and batch.institution_id != institution.id:
        raise ValidationError({"batch_id": "Batch does not belong to the profile institution."})
    return batch


def _get_guardian(guardian_profile_id):
    if not guardian_profile_id:
        return None
    try:
        return UserProfile.objects.get(id=guardian_profile_id, deleted_at__isnull=True)
    except UserProfile.DoesNotExist as exc:
        raise ValidationError({"guardian_profile_id": "Guardian profile was not found."}) from exc


def create_institution(*, validated_data: dict[str, Any]) -> Institution:
    return Institution.objects.create(
        name=validated_data["name"],
        code=validated_data["code"],
        status=validated_data.get("status", InstitutionStatus.ACTIVE),
        settings=validated_data.get("settings", {}),
    )


def update_institution(*, institution: Institution, validated_data: dict[str, Any]) -> Institution:
    for field in ["name", "code", "status", "settings"]:
        if field in validated_data:
            setattr(institution, field, validated_data[field])
    institution.save()
    return institution


def archive_institution(*, institution: Institution) -> Institution:
    institution.status = InstitutionStatus.ARCHIVED
    institution.deleted_at = timezone.now()
    institution.save(update_fields=["status", "deleted_at", "updated_at"])
    return institution


def create_department(*, validated_data: dict[str, Any]) -> Department:
    institution = _get_institution(validated_data["institution_id"])
    return Department.objects.create(
        institution=institution,
        name=validated_data["name"],
        code=validated_data["code"],
        status=validated_data.get("status", DepartmentStatus.ACTIVE),
    )


def update_department(*, department: Department, validated_data: dict[str, Any]) -> Department:
    for field in ["name", "code", "status"]:
        if field in validated_data:
            setattr(department, field, validated_data[field])
    department.save()
    return department


def archive_department(*, department: Department) -> Department:
    department.status = DepartmentStatus.ARCHIVED
    department.deleted_at = timezone.now()
    department.save(update_fields=["status", "deleted_at", "updated_at"])
    return department


def create_batch(*, validated_data: dict[str, Any]) -> Batch:
    institution = _get_institution(validated_data["institution_id"])
    department = _get_department(validated_data.get("department_id"), institution)
    return Batch.objects.create(
        institution=institution,
        department=department,
        name=validated_data["name"],
        start_date=validated_data.get("start_date"),
        end_date=validated_data.get("end_date"),
        status=validated_data.get("status", BatchStatus.ACTIVE),
    )


def update_batch(*, batch: Batch, validated_data: dict[str, Any]) -> Batch:
    if "department_id" in validated_data:
        batch.department = _get_department(validated_data.get("department_id"), batch.institution)
    for field in ["name", "start_date", "end_date", "status"]:
        if field in validated_data:
            setattr(batch, field, validated_data[field])
    batch.save()
    return batch


def archive_batch(*, batch: Batch) -> Batch:
    batch.status = BatchStatus.ARCHIVED
    batch.deleted_at = timezone.now()
    batch.save(update_fields=["status", "deleted_at", "updated_at"])
    return batch


def _role_for_profile(validated_data: dict[str, Any]) -> str:
    role_code = validated_data.get("role_code")
    if role_code:
        return role_code
    if validated_data["profile_type"] == "admin":
        admin_type = validated_data.get("admin", {}).get("admin_type", AdminType.INSTITUTION_ADMIN)
        return "super_admin" if admin_type == AdminType.SUPER_ADMIN else "institution_admin"
    return validated_data["profile_type"]


def _create_role_profile(profile: UserProfile, validated_data: dict[str, Any]) -> None:
    institution = profile.institution
    profile_type = validated_data["profile_type"]
    if profile_type == "student":
        student = validated_data["student"]
        StudentProfile.objects.create(
            user_profile=profile,
            student_number=student["student_number"],
            batch=_get_batch(student.get("batch_id"), institution),
            department=_get_department(student.get("department_id"), institution),
            guardian_profile=_get_guardian(student.get("guardian_profile_id")),
        )
    elif profile_type == "instructor":
        instructor = validated_data.get("instructor", {})
        InstructorProfile.objects.create(
            user_profile=profile,
            employee_number=instructor.get("employee_number") or None,
            department=_get_department(instructor.get("department_id"), institution),
            title=instructor.get("title") or None,
            bio=instructor.get("bio") or None,
        )
    elif profile_type == "admin":
        admin = validated_data.get("admin", {})
        AdminProfile.objects.create(
            user_profile=profile,
            admin_type=admin.get("admin_type", AdminType.INSTITUTION_ADMIN),
            department=_get_department(admin.get("department_id"), institution),
        )


def create_user_profile(*, validated_data: dict[str, Any], token: str) -> UserProfile:
    institution = _get_institution(validated_data.get("institution_id"))
    scope_type, scope_id = _scope_for_institution(validated_data.get("institution_id"))
    role_code = _role_for_profile(validated_data)

    auth_account = create_auth_account(
        token=token,
        email=validated_data["email"],
        phone=validated_data.get("phone"),
        temporary_password=validated_data["temporary_password"],
        role_code=role_code,
        scope_type=scope_type,
        scope_id=scope_id,
    )

    try:
        with transaction.atomic():
            profile = UserProfile.objects.create(
                auth_account_id=auth_account["id"],
                institution=institution,
                first_name=validated_data["first_name"],
                last_name=validated_data["last_name"],
                display_name=validated_data.get("display_name"),
                avatar_url=validated_data.get("avatar_url"),
                metadata=validated_data.get("metadata", {}),
            )
            _create_role_profile(profile, validated_data)
            return get_profile(profile.id)
    except Exception as exc:
        try:
            deactivate_auth_account(
                token=token,
                auth_account_id=auth_account["id"],
                scope_type=scope_type,
                scope_id=scope_id,
            )
        except AuthServiceError:
            pass
        if isinstance(exc, IntegrityError):
            raise ValidationError({"auth_account_id": "A profile already exists for this account."}) from exc
        if isinstance(exc, ObjectDoesNotExist):
            raise ValidationError("Referenced profile data was not found.") from exc
        raise


def _update_role_profile(profile: UserProfile, validated_data: dict[str, Any]) -> None:
    if "student" in validated_data and hasattr(profile, "student_profile"):
        student = profile.student_profile
        payload = validated_data["student"]
        if "student_number" in payload:
            student.student_number = payload["student_number"]
        if "batch_id" in payload:
            student.batch = _get_batch(payload.get("batch_id"), profile.institution)
        if "department_id" in payload:
            student.department = _get_department(payload.get("department_id"), profile.institution)
        if "guardian_profile_id" in payload:
            student.guardian_profile = _get_guardian(payload.get("guardian_profile_id"))
        student.save()
    if "instructor" in validated_data and hasattr(profile, "instructor_profile"):
        instructor = profile.instructor_profile
        payload = validated_data["instructor"]
        if "employee_number" in payload:
            instructor.employee_number = payload.get("employee_number") or None
        if "department_id" in payload:
            instructor.department = _get_department(payload.get("department_id"), profile.institution)
        if "title" in payload:
            instructor.title = payload.get("title") or None
        if "bio" in payload:
            instructor.bio = payload.get("bio") or None
        instructor.save()
    if "admin" in validated_data and hasattr(profile, "admin_profile"):
        admin = profile.admin_profile
        payload = validated_data["admin"]
        if "admin_type" in payload:
            admin.admin_type = payload["admin_type"]
        if "department_id" in payload:
            admin.department = _get_department(payload.get("department_id"), profile.institution)
        admin.save()


def update_user_profile(*, profile: UserProfile, validated_data: dict[str, Any], token: str) -> UserProfile:
    scope_type, scope_id = _scope_for_institution(profile.institution_id)
    if "email" in validated_data or "phone" in validated_data:
        update_auth_account(
            token=token,
            auth_account_id=profile.auth_account_id,
            scope_type=scope_type,
            scope_id=scope_id,
            email=validated_data.get("email"),
            phone=validated_data.get("phone"),
        )

    profile_fields = [
        "first_name",
        "last_name",
        "display_name",
        "avatar_url",
        "status",
        "metadata",
    ]
    with transaction.atomic():
        for field in profile_fields:
            if field in validated_data:
                setattr(profile, field, validated_data[field])
        profile.save()
        _update_role_profile(profile, validated_data)
    return get_profile(profile.id)


def deactivate_user_profile(*, profile: UserProfile, token: str) -> UserProfile:
    scope_type, scope_id = _scope_for_institution(profile.institution_id)
    deactivate_auth_account(
        token=token,
        auth_account_id=profile.auth_account_id,
        scope_type=scope_type,
        scope_id=scope_id,
    )
    profile.status = UserProfileStatus.DEACTIVATED
    profile.deleted_at = timezone.now()
    profile.save(update_fields=["status", "deleted_at", "updated_at"])
    return get_profile(profile.id)


def get_profile(profile_id) -> UserProfile:
    return (
        UserProfile.objects.select_related("institution")
        .select_related(
            "student_profile__batch",
            "student_profile__department",
            "student_profile__guardian_profile",
            "instructor_profile__department",
            "admin_profile__department",
        )
        .get(id=profile_id)
    )
