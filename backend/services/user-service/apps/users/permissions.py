from __future__ import annotations

from learngrid_authz import RemoteAuthorizationPermission, remote_authorization_check
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

__all__ = [
    "ProfileManagePermission",
    "ProfileViewPermission",
    "RemoteAuthorizationPermission",
    "profile_scope_from_institution",
    "remote_authorization_check",
    "require_institution_manage_permission",
    "require_profile_permission",
]


def profile_scope_from_institution(institution_id) -> tuple[str, str | None]:
    if institution_id:
        return "institution", str(institution_id)
    return "platform", None


def require_profile_permission(request, permission: str, institution_id=None) -> None:
    if not request.user or not request.user.is_authenticated or not isinstance(request.auth, str):
        raise PermissionDenied("Authentication is required.")
    scope_type, scope_id = profile_scope_from_institution(institution_id)
    if not remote_authorization_check(
        token=request.auth,
        permission=permission,
        scope_type=scope_type,
        scope_id=scope_id,
    ):
        raise PermissionDenied("You do not have permission to access this profile scope.")


def require_institution_manage_permission(request, institution_id=None) -> None:
    if not request.user or not request.user.is_authenticated or not isinstance(request.auth, str):
        raise PermissionDenied("Authentication is required.")
    scope_type, scope_id = profile_scope_from_institution(institution_id)
    if not remote_authorization_check(
        token=request.auth,
        permission="institution.manage",
        scope_type=scope_type,
        scope_id=scope_id,
    ):
        raise PermissionDenied("You do not have permission to manage this institution scope.")


class ProfileViewPermission(BasePermission):
    def has_permission(self, request, _view) -> bool:
        institution_id = request.query_params.get("institution_id") or request.data.get(
            "institution_id"
        )
        try:
            require_profile_permission(request, "profile.view", institution_id)
        except PermissionDenied:
            return False
        return True


class ProfileManagePermission(BasePermission):
    def has_permission(self, request, _view) -> bool:
        institution_id = request.query_params.get("institution_id") or request.data.get(
            "institution_id"
        )
        try:
            require_profile_permission(request, "profile.manage", institution_id)
        except PermissionDenied:
            return False
        return True
