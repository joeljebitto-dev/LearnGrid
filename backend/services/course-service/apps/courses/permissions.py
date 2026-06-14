from __future__ import annotations

from learngrid_authz import RemoteAuthorizationPermission, remote_authorization_check
from rest_framework.exceptions import PermissionDenied

__all__ = [
    "RemoteAuthorizationPermission",
    "course_scope_from_institution",
    "has_course_permission",
    "remote_authorization_check",
    "require_course_permission",
]


def course_scope_from_institution(institution_id) -> tuple[str, str | None]:
    if institution_id:
        return "institution", str(institution_id)
    return "platform", None


def has_course_permission(request, permission: str, institution_id=None) -> bool:
    if not request.user or not request.user.is_authenticated or not isinstance(request.auth, str):
        return False
    scope_type, scope_id = course_scope_from_institution(institution_id)
    return remote_authorization_check(
        token=request.auth,
        permission=permission,
        scope_type=scope_type,
        scope_id=scope_id,
    )


def require_course_permission(request, permission: str, institution_id=None) -> None:
    if not has_course_permission(request, permission, institution_id):
        raise PermissionDenied("You do not have permission to access this course scope.")
