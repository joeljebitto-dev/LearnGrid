import uuid

from django.db import models
from django.utils import timezone


class AccountStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACTIVE = "active", "Active"
    LOCKED = "locked", "Locked"
    DISABLED = "disabled", "Disabled"
    DEACTIVATED = "deactivated", "Deactivated"


class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32, unique=True, null=True, blank=True)
    status = models.CharField(
        max_length=24,
        choices=AccountStatus.choices,
        default=AccountStatus.PENDING,
    )
    is_staff = models.BooleanField(default=False)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts"
        indexes = [
            models.Index(fields=["status"], name="idx_accounts_status"),
            models.Index(fields=["deleted_at"], name="idx_accounts_deleted_at"),
        ]

    @property
    def is_active(self) -> bool:
        return self.status == AccountStatus.ACTIVE and self.deleted_at is None

    @property
    def is_authenticated(self) -> bool:
        return True

    def __str__(self) -> str:
        return self.email


class Credential(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name="credential")
    password_hash = models.TextField()
    password_changed_at = models.DateTimeField(default=timezone.now)
    must_change_password = models.BooleanField(default=False)
    failed_attempt_count = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "credentials"
        indexes = [models.Index(fields=["locked_until"], name="idx_credentials_locked_until")]


class RefreshToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="refresh_tokens")
    token_jti = models.UUIDField(unique=True)
    token_hash = models.TextField()
    issued_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    device_label = models.CharField(max_length=128, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "refresh_tokens"
        indexes = [
            models.Index(fields=["account"], name="idx_refresh_tokens_account_id"),
            models.Index(fields=["expires_at"], name="idx_refresh_tokens_expires_at"),
        ]

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None and self.expires_at > timezone.now()


class BlacklistReason(models.TextChoices):
    LOGOUT = "logout", "Logout"
    ROTATION = "rotation", "Rotation"
    ADMIN_REVOKE = "admin_revoke", "Admin revoke"
    PASSWORD_CHANGE = "password_change", "Password change"
    COMPROMISED = "compromised", "Compromised"


class TokenBlacklist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token_jti = models.UUIDField(unique=True)
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="blacklisted_tokens",
        null=True,
        blank=True,
    )
    reason = models.CharField(
        max_length=64,
        choices=BlacklistReason.choices,
        default=BlacklistReason.LOGOUT,
    )
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "token_blacklist"
        indexes = [models.Index(fields=["expires_at"], name="idx_token_blacklist_expires_at")]


class PasswordResetStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    USED = "used", "Used"
    EXPIRED = "expired", "Expired"
    REVOKED = "revoked", "Revoked"


class PasswordResetToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token_hash = models.TextField()
    status = models.CharField(
        max_length=24,
        choices=PasswordResetStatus.choices,
        default=PasswordResetStatus.PENDING,
    )
    requested_ip = models.GenericIPAddressField(null=True, blank=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "password_reset_tokens"
        indexes = [
            models.Index(fields=["account"], name="idx_password_reset_account_id"),
            models.Index(fields=["status", "expires_at"], name="idx_password_reset_status_exp"),
        ]


class LoginAuditEvent(models.TextChoices):
    LOGIN_SUCCESS = "login_success", "Login success"
    LOGIN_FAILURE = "login_failure", "Login failure"
    LOGOUT = "logout", "Logout"
    TOKEN_REFRESH = "token_refresh", "Token refresh"
    PASSWORD_RESET = "password_reset", "Password reset"


class LoginAuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        related_name="login_audit_logs",
        null=True,
        blank=True,
    )
    email_attempted = models.EmailField(null=True, blank=True)
    event_type = models.CharField(max_length=40, choices=LoginAuditEvent.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "login_audit_logs"
        indexes = [
            models.Index(fields=["account", "created_at"], name="idx_login_audit_account_ts"),
            models.Index(fields=["event_type"], name="idx_login_audit_event_type"),
            models.Index(fields=["email_attempted"], name="idx_login_audit_email"),
        ]


class RoleScopeType(models.TextChoices):
    PLATFORM = "platform", "Platform"
    INSTITUTION = "institution", "Institution"
    COURSE = "course", "Course"


class AssignmentScopeType(models.TextChoices):
    PLATFORM = "platform", "Platform"
    INSTITUTION = "institution", "Institution"
    COURSE = "course", "Course"
    ASSESSMENT = "assessment", "Assessment"


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    scope_type = models.CharField(
        max_length=32,
        choices=RoleScopeType.choices,
        default=RoleScopeType.INSTITUTION,
    )
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "roles"
        indexes = [models.Index(fields=["scope_type"], name="idx_roles_scope_type")]

    def __str__(self) -> str:
        return self.code


class Permission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=128, unique=True)
    resource = models.CharField(max_length=64)
    action = models.CharField(max_length=64)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "permissions"
        indexes = [models.Index(fields=["resource", "action"], name="idx_perm_resource_action")]

    def __str__(self) -> str:
        return self.code


class RolePermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "role_permissions"
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"],
                name="uq_role_perm_role_permission",
            )
        ]
        indexes = [models.Index(fields=["permission"], name="idx_role_perm_permission")]


class RoleAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="role_assignments")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_assignments")
    scope_type = models.CharField(
        max_length=32,
        choices=AssignmentScopeType.choices,
        default=AssignmentScopeType.PLATFORM,
    )
    scope_id = models.UUIDField(null=True, blank=True)
    assigned_by_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        related_name="assigned_role_assignments",
        null=True,
        blank=True,
    )
    assigned_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "role_assignments"
        constraints = [
            models.UniqueConstraint(
                fields=["account", "role", "scope_type"],
                condition=models.Q(revoked_at__isnull=True, scope_id__isnull=True),
                name="uq_active_role_assign_platform",
            ),
            models.UniqueConstraint(
                fields=["account", "role", "scope_type", "scope_id"],
                condition=models.Q(revoked_at__isnull=True, scope_id__isnull=False),
                name="uq_active_role_assign_scoped",
            ),
        ]
        indexes = [
            models.Index(fields=["account"], name="idx_role_assign_account"),
            models.Index(fields=["scope_type", "scope_id"], name="idx_role_assign_scope"),
        ]

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None


class AuthorizationAuditEvent(models.TextChoices):
    ROLE_ASSIGNMENT_CREATED = "role_assignment_created", "Role assignment created"
    ROLE_ASSIGNMENT_REVOKED = "role_assignment_revoked", "Role assignment revoked"
    ROLE_PERMISSION_GRANTED = "role_permission_granted", "Role permission granted"
    ROLE_PERMISSION_REVOKED = "role_permission_revoked", "Role permission revoked"


class AuthorizationAuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        related_name="authorization_audit_actions",
        null=True,
        blank=True,
    )
    target_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        related_name="authorization_audit_targets",
        null=True,
        blank=True,
    )
    event_type = models.CharField(max_length=64, choices=AuthorizationAuditEvent.choices)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    permission = models.ForeignKey(Permission, on_delete=models.SET_NULL, null=True, blank=True)
    role_assignment = models.ForeignKey(
        RoleAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    scope_type = models.CharField(max_length=32, blank=True)
    scope_id = models.UUIDField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "authorization_audit_logs"
        indexes = [
            models.Index(
                fields=["actor_account", "created_at"], name="idx_auth_audit_actor_created"
            ),
            models.Index(fields=["target_account"], name="idx_auth_audit_target"),
            models.Index(fields=["event_type"], name="idx_auth_audit_event_type"),
        ]
