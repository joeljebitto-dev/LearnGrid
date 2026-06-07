from rest_framework import serializers

from .models import Account, AccountStatus, AssignmentScopeType, Permission, Role, RoleAssignment


class TokenIssueSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False, write_only=True)
    device_label = serializers.CharField(required=False, allow_blank=True, max_length=128)


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField(trim_whitespace=False)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(trim_whitespace=False)
    access = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "code", "name", "scope_type", "is_system"]


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "code", "resource", "action", "description"]


class RoleAssignmentSerializer(serializers.ModelSerializer):
    account_id = serializers.UUIDField(source="account.id", read_only=True)
    role_code = serializers.CharField(source="role.code", read_only=True)
    assigned_by_account_id = serializers.UUIDField(source="assigned_by_account.id", read_only=True)

    class Meta:
        model = RoleAssignment
        fields = [
            "id",
            "account_id",
            "role_code",
            "scope_type",
            "scope_id",
            "assigned_by_account_id",
            "assigned_at",
            "revoked_at",
        ]


class RoleAssignmentCreateSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    role_code = serializers.CharField(max_length=64)
    scope_type = serializers.ChoiceField(choices=AssignmentScopeType.choices)
    scope_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        scope_type = attrs["scope_type"]
        scope_id = attrs.get("scope_id")
        if scope_type == AssignmentScopeType.PLATFORM:
            attrs["scope_id"] = None
        elif scope_id is None:
            raise serializers.ValidationError({"scope_id": "scope_id is required for scoped roles."})
        return attrs


class AuthorizationCheckSerializer(serializers.Serializer):
    permission = serializers.CharField(max_length=128)
    scope_type = serializers.ChoiceField(
        choices=AssignmentScopeType.choices,
        default=AssignmentScopeType.PLATFORM,
    )
    scope_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        scope_type = attrs.get("scope_type", AssignmentScopeType.PLATFORM)
        scope_id = attrs.get("scope_id")
        if scope_type == AssignmentScopeType.PLATFORM:
            attrs["scope_id"] = None
        elif scope_id is None:
            raise serializers.ValidationError({"scope_id": "scope_id is required for scoped checks."})
        return attrs


class AccountSerializer(serializers.ModelSerializer):
    must_change_password = serializers.BooleanField(source="credential.must_change_password", read_only=True)

    class Meta:
        model = Account
        fields = [
            "id",
            "email",
            "phone",
            "status",
            "must_change_password",
            "created_at",
            "updated_at",
            "deleted_at",
        ]


class AccountCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone = serializers.CharField(required=False, allow_blank=True, max_length=32)
    temporary_password = serializers.CharField(write_only=True, trim_whitespace=False, min_length=8)
    role_code = serializers.CharField(required=False, allow_blank=True, max_length=64)
    scope_type = serializers.ChoiceField(
        choices=AssignmentScopeType.choices,
        default=AssignmentScopeType.PLATFORM,
    )
    scope_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        scope_type = attrs.get("scope_type", AssignmentScopeType.PLATFORM)
        scope_id = attrs.get("scope_id")
        role_code = attrs.get("role_code")
        if scope_type == AssignmentScopeType.PLATFORM:
            attrs["scope_id"] = None
        elif scope_id is None:
            raise serializers.ValidationError({"scope_id": "scope_id is required for scoped accounts."})
        if role_code and not Role.objects.filter(code=role_code).exists():
            raise serializers.ValidationError({"role_code": "Role was not found."})
        attrs["role_code"] = role_code or None
        attrs["phone"] = attrs.get("phone") or None
        return attrs


class AccountUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=32)
    status = serializers.ChoiceField(choices=AccountStatus.choices, required=False)
    scope_type = serializers.ChoiceField(
        choices=AssignmentScopeType.choices,
        default=AssignmentScopeType.PLATFORM,
    )
    scope_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        scope_type = attrs.get("scope_type", AssignmentScopeType.PLATFORM)
        scope_id = attrs.get("scope_id")
        if scope_type == AssignmentScopeType.PLATFORM:
            attrs["scope_id"] = None
        elif scope_id is None:
            raise serializers.ValidationError({"scope_id": "scope_id is required for scoped accounts."})
        return attrs


class AccountDeactivateSerializer(serializers.Serializer):
    scope_type = serializers.ChoiceField(
        choices=AssignmentScopeType.choices,
        default=AssignmentScopeType.PLATFORM,
    )
    scope_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        scope_type = attrs.get("scope_type", AssignmentScopeType.PLATFORM)
        scope_id = attrs.get("scope_id")
        if scope_type == AssignmentScopeType.PLATFORM:
            attrs["scope_id"] = None
        elif scope_id is None:
            raise serializers.ValidationError({"scope_id": "scope_id is required for scoped accounts."})
        return attrs
