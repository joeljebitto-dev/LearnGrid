from __future__ import annotations

from learngrid_authz import RemoteAuthorizationPermission, remote_authorization_check
from rest_framework.exceptions import PermissionDenied

__all__ = [
    "RemoteAuthorizationPermission",
    "has_grade_permission",
    "remote_authorization_check",
    "require_grade_permission",
]


def has_grade_permission(request, permission: str, *, course_id=None, institution_id=None) -> bool:
    if not request.user or not request.user.is_authenticated or not isinstance(request.auth, str):
        return False
    if course_id and remote_authorization_check(
        token=request.auth,
        permission=permission,
        scope_type="course",
        scope_id=str(course_id),
    ):
        return True
    if institution_id:
        return remote_authorization_check(
            token=request.auth,
            permission=permission,
            scope_type="institution",
            scope_id=str(institution_id),
        )
    return remote_authorization_check(
        token=request.auth,
        permission=permission,
        scope_type="platform",
        scope_id=None,
    )


def require_grade_permission(
    request, permission: str, *, course_id=None, institution_id=None
) -> None:
    if not has_grade_permission(
        request,
        permission,
        course_id=course_id,
        institution_id=institution_id,
    ):
        raise PermissionDenied("You do not have permission to access this grade scope.")
