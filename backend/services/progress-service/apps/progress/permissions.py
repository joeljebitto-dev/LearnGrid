from __future__ import annotations

from learngrid_authz import RemoteAuthorizationPermission, remote_authorization_check
from rest_framework.exceptions import PermissionDenied

__all__ = [
    "RemoteAuthorizationPermission",
    "has_progress_permission",
    "remote_authorization_check",
    "require_progress_permission",
]


def has_progress_permission(request, permission: str, scope_id=None) -> bool:
    if not request.user or not request.user.is_authenticated or not isinstance(request.auth, str):
        return False
    return remote_authorization_check(
        token=request.auth,
        permission=permission,
        scope_type="course" if scope_id else "platform",
        scope_id=str(scope_id) if scope_id else None,
    )


def require_progress_permission(request, permission: str, scope_id=None) -> None:
    if not has_progress_permission(request, permission, scope_id):
        raise PermissionDenied("You do not have permission to access this progress scope.")
