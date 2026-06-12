from __future__ import annotations

import json
from urllib import error, request as urlrequest

from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


def remote_authorization_check(
    *,
    token: str,
    permission: str,
    scope_type: str = "platform",
    scope_id: str | None = None,
) -> bool:
    payload = {"permission": permission, "scope_type": scope_type, "scope_id": scope_id}
    request = urlrequest.Request(
        f"{settings.AUTH_SERVICE_BASE_URL.rstrip('/')}/api/auth/authorization/check/",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(request, timeout=2) as response:
            if response.status >= 400:
                return False
            body = json.loads(response.read().decode("utf-8"))
            return body.get("allowed") is True
    except (error.HTTPError, error.URLError, TimeoutError, OSError, ValueError):
        return False


class RemoteAuthorizationPermission(BasePermission):
    required_permission: str | None = None
    scope_type = "platform"

    def get_required_permission(self, view) -> str | None:
        return getattr(view, "required_permission", self.required_permission)

    def get_scope_type(self, view) -> str:
        return getattr(view, "required_scope_type", self.scope_type)

    def get_scope_id(self, request, view, scope_type: str) -> str | None:
        explicit_scope_id = getattr(view, "required_scope_id", None)
        if explicit_scope_id:
            return str(explicit_scope_id)

        lookup_key = f"{scope_type}_id"
        kwargs = getattr(view, "kwargs", {}) or getattr(request, "parser_context", {}).get(
            "kwargs", {}
        )
        if lookup_key in kwargs:
            return str(kwargs[lookup_key])
        if "scope_id" in kwargs:
            return str(kwargs["scope_id"])

        data = getattr(request, "data", {})
        if lookup_key in data:
            return str(data[lookup_key])
        if "scope_id" in data:
            return str(data["scope_id"])

        query_params = getattr(request, "query_params", {})
        if lookup_key in query_params:
            return str(query_params[lookup_key])
        return query_params.get("scope_id")

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        permission = self.get_required_permission(view)
        if not permission or not isinstance(request.auth, str):
            return False
        scope_type = self.get_scope_type(view)
        return remote_authorization_check(
            token=request.auth,
            permission=permission,
            scope_type=scope_type,
            scope_id=self.get_scope_id(request, view, scope_type),
        )


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
