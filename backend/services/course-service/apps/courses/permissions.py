from __future__ import annotations

from learngrid_authz import RemoteAuthorizationPermission, remote_authorization_check
from rest_framework.exceptions import PermissionDenied

__all__ = [
    "RemoteAuthorizationPermission",
    "course_scope_from_institution",
    "has_assigned_course_permission",
    "has_course_permission",
    "remote_authorization_check",
    "require_assigned_course_permission",
    "require_course_permission",
]


def course_scope_from_institution(institution_id) -> tuple[str, str | None]:
    if institution_id:
        return "institution", str(institution_id)
    return "platform", None


def has_scoped_course_permission(
    request,
    permission: str,
    *,
    scope_type: str,
    scope_id=None,
) -> bool:
    if not request.user or not request.user.is_authenticated or not isinstance(request.auth, str):
        return False
    return remote_authorization_check(
        token=request.auth,
        permission=permission,
        scope_type=scope_type,
        scope_id=str(scope_id) if scope_id is not None else None,
    )


def has_course_permission(request, permission: str, institution_id=None) -> bool:
    scope_type, scope_id = course_scope_from_institution(institution_id)
    return has_scoped_course_permission(
        request,
        permission,
        scope_type=scope_type,
        scope_id=scope_id,
    )


def has_assigned_course_permission(request, permission: str, course_id) -> bool:
    return has_scoped_course_permission(
        request,
        permission,
        scope_type="course",
        scope_id=course_id,
    )


def require_course_permission(request, permission: str, institution_id=None) -> None:
    if not has_course_permission(request, permission, institution_id):
        raise PermissionDenied("You do not have permission to access this course scope.")


def require_assigned_course_permission(request, permission: str, course_id) -> None:
    if not has_assigned_course_permission(request, permission, course_id):
        raise PermissionDenied("You do not have permission to access this course.")
