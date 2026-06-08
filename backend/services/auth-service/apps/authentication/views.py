from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from .models import Account, AssignmentScopeType, Permission, Role, RoleAssignment
from .permissions import CanManageRbac
from .serializers import (
    AccountCreateSerializer,
    AccountDeactivateSerializer,
    AccountSerializer,
    AccountUpdateSerializer,
    AuthorizationCheckSerializer,
    LogoutSerializer,
    PermissionSerializer,
    RoleAssignmentCreateSerializer,
    RoleAssignmentSerializer,
    RoleSerializer,
    TokenIssueSerializer,
    TokenRefreshSerializer,
)
from .services import (
    assign_role,
    create_managed_account,
    deactivate_managed_account,
    has_active_role,
    has_permission,
    issue_token_pair_for_credentials,
    logout_tokens,
    refresh_token_pair,
    require_permission,
    revoke_role_assignment,
    update_managed_account,
)


class TokenIssueView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = TokenIssueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_pair = issue_token_pair_for_credentials(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            device_label=serializer.validated_data.get("device_label") or None,
            request=request,
        )
        return Response(token_pair.as_response())


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_pair = refresh_token_pair(serializer.validated_data["refresh"], request=request)
        return Response(token_pair.as_response())


class LogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        logout_tokens(
            refresh_token=serializer.validated_data["refresh"],
            access_token=serializer.validated_data.get("access") or None,
            request=request,
        )
        return Response({"status": "revoked"})


class SessionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        account = request.user
        assignments = list(
            RoleAssignment.objects.select_related("role").filter(
                account=account,
                revoked_at__isnull=True,
            ).order_by("assigned_at", "id")
        )
        role_precedence = [
            "super_admin",
            "institution_admin",
            "instructor",
            "teaching_assistant",
            "student",
            "parent_guardian",
        ]
        active_role_codes = {assignment.role.code for assignment in assignments}
        primary_role = next(
            (role_code for role_code in role_precedence if role_code in active_role_codes),
            None,
        )
        return Response(
            {
                "account_id": str(account.id),
                "email": account.email,
                "status": account.status,
                "primary_role": primary_role,
                "role_assignments": [
                    {
                        "id": str(assignment.id),
                        "role_code": assignment.role.code,
                        "role_name": assignment.role.name,
                        "scope_type": assignment.scope_type,
                        "scope_id": str(assignment.scope_id) if assignment.scope_id else None,
                        "assigned_at": assignment.assigned_at.isoformat(),
                    }
                    for assignment in assignments
                ],
            }
        )


class RoleListView(APIView):
    permission_classes = [CanManageRbac]

    def get(self, _request):
        roles = Role.objects.order_by("code")
        return Response(RoleSerializer(roles, many=True).data)


class PermissionListView(APIView):
    permission_classes = [CanManageRbac]

    def get(self, _request):
        permissions = Permission.objects.order_by("resource", "action")
        return Response(PermissionSerializer(permissions, many=True).data)


class RoleAssignmentCreateView(APIView):
    permission_classes = [CanManageRbac]

    def post(self, request):
        serializer = RoleAssignmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        account = get_object_or_404(Account, id=serializer.validated_data["account_id"])
        role = get_object_or_404(Role, code=serializer.validated_data["role_code"])
        scope_type = serializer.validated_data["scope_type"]
        if scope_type == AssignmentScopeType.PLATFORM and not has_active_role(
            request.user,
            "super_admin",
        ):
            raise PermissionDenied("Only Super Admin users can create platform assignments.")

        assignment = assign_role(
            account=account,
            role=role,
            scope_type=scope_type,
            scope_id=serializer.validated_data.get("scope_id"),
            assigned_by_account=request.user,
            request=request,
        )
        return Response(RoleAssignmentSerializer(assignment).data, status=201)


class RoleAssignmentDeleteView(APIView):
    permission_classes = [CanManageRbac]

    def delete(self, request, assignment_id):
        assignment = get_object_or_404(
            RoleAssignment.objects.select_related("account", "role"),
            id=assignment_id,
        )
        revoke_role_assignment(assignment, revoked_by_account=request.user, request=request)
        return Response({"status": "revoked"})


class AuthorizationCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AuthorizationCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        allowed = has_permission(
            request.user,
            serializer.validated_data["permission"],
            scope_type=serializer.validated_data["scope_type"],
            scope_id=serializer.validated_data.get("scope_id"),
        )
        return Response({"allowed": allowed})


def _require_account_scope_permission(request, scope_type, scope_id) -> None:
    require_permission(
        request.user,
        "profile.manage",
        scope_type=scope_type,
        scope_id=scope_id,
    )
    if scope_type == AssignmentScopeType.PLATFORM and not has_active_role(request.user, "super_admin"):
        raise PermissionDenied("Only Super Admin users can perform platform account operations.")


class AccountCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AccountCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        scope_type = serializer.validated_data["scope_type"]
        scope_id = serializer.validated_data.get("scope_id")
        _require_account_scope_permission(request, scope_type, scope_id)

        account = create_managed_account(
            email=serializer.validated_data["email"],
            phone=serializer.validated_data.get("phone"),
            temporary_password=serializer.validated_data["temporary_password"],
            role_code=serializer.validated_data.get("role_code"),
            scope_type=scope_type,
            scope_id=scope_id,
            actor_account=request.user,
            request=request,
        )
        return Response(AccountSerializer(account).data, status=201)


class AccountDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, account_id):
        serializer = AccountUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        scope_type = serializer.validated_data["scope_type"]
        scope_id = serializer.validated_data.get("scope_id")
        _require_account_scope_permission(request, scope_type, scope_id)

        account = get_object_or_404(Account.objects.select_related("credential"), id=account_id)
        update_kwargs = {
            field: serializer.validated_data[field]
            for field in ("email", "phone", "status")
            if field in serializer.validated_data
        }
        account = update_managed_account(
            account,
            **update_kwargs,
        )
        return Response(AccountSerializer(account).data)


class AccountDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, account_id):
        serializer = AccountDeactivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        scope_type = serializer.validated_data["scope_type"]
        scope_id = serializer.validated_data.get("scope_id")
        _require_account_scope_permission(request, scope_type, scope_id)

        account = get_object_or_404(Account.objects.select_related("credential"), id=account_id)
        account = deactivate_managed_account(account)
        return Response(AccountSerializer(account).data)
