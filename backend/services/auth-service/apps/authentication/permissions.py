from rest_framework.permissions import BasePermission

from .services import has_active_role, has_permission


class HasRbacPermission(BasePermission):
    required_permission: str | None = None
    scope_type = "platform"
    scope_id = None

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        permission_code = self.required_permission or getattr(view, "required_permission", None)
        if not permission_code:
            return False

        scope_type = getattr(view, "required_scope_type", self.scope_type)
        scope_id = getattr(view, "required_scope_id", self.scope_id)
        return has_permission(
            request.user,
            permission_code,
            scope_type=scope_type,
            scope_id=scope_id,
        )


class CanManageRbac(HasRbacPermission):
    required_permission = "rbac.manage"


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, _view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        return has_active_role(request.user, "super_admin")
