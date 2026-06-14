from __future__ import annotations

from learngrid_authz import RemoteAuthorizationPermission, remote_authorization_check
from rest_framework.exceptions import PermissionDenied

__all__ = [
    "RemoteAuthorizationPermission",
    "has_notification_permission",
    "remote_authorization_check",
    "require_notification_permission",
]


def has_notification_permission(request, permission: str) -> bool:
    if not request.user or not request.user.is_authenticated or not isinstance(request.auth, str):
        return False
    return remote_authorization_check(
        token=request.auth,
        permission=permission,
        scope_type="platform",
        scope_id=None,
    )


def require_notification_permission(request, permission: str) -> None:
    if not has_notification_permission(request, permission):
        raise PermissionDenied("You do not have permission to access this notification resource.")
