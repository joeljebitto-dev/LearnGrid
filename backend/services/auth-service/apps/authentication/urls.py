from django.urls import path

from .views import (
    AccountCreateView,
    AccountDeactivateView,
    AccountDetailView,
    AuthorizationCheckView,
    LogoutView,
    PermissionListView,
    RoleAssignmentCreateView,
    RoleAssignmentDeleteView,
    RoleListView,
    SessionView,
    TokenIssueView,
    TokenRefreshView,
)

urlpatterns = [
    path("token/issue/", TokenIssueView.as_view(), name="token-issue"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("session/", SessionView.as_view(), name="session"),
    path("accounts/", AccountCreateView.as_view(), name="account-create"),
    path("accounts/<uuid:account_id>/", AccountDetailView.as_view(), name="account-detail"),
    path(
        "accounts/<uuid:account_id>/deactivate/",
        AccountDeactivateView.as_view(),
        name="account-deactivate",
    ),
    path("rbac/roles/", RoleListView.as_view(), name="rbac-roles"),
    path("rbac/permissions/", PermissionListView.as_view(), name="rbac-permissions"),
    path(
        "rbac/role-assignments/",
        RoleAssignmentCreateView.as_view(),
        name="rbac-role-assignment-create",
    ),
    path(
        "rbac/role-assignments/<uuid:assignment_id>/",
        RoleAssignmentDeleteView.as_view(),
        name="rbac-role-assignment-delete",
    ),
    path("authorization/check/", AuthorizationCheckView.as_view(), name="authorization-check"),
]
