# Generated for LearnGrid LMS T-002 token and session security.

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Account",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("phone", models.CharField(blank=True, max_length=32, null=True, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("active", "Active"),
                            ("locked", "Locked"),
                            ("disabled", "Disabled"),
                            ("deactivated", "Deactivated"),
                        ],
                        default="pending",
                        max_length=24,
                    ),
                ),
                ("is_staff", models.BooleanField(default=False)),
                ("last_login_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "accounts",
                "indexes": [
                    models.Index(fields=["status"], name="idx_accounts_status"),
                    models.Index(fields=["deleted_at"], name="idx_accounts_deleted_at"),
                ],
            },
        ),
        migrations.CreateModel(
            name="Credential",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("password_hash", models.TextField()),
                ("password_changed_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("must_change_password", models.BooleanField(default=False)),
                ("failed_attempt_count", models.IntegerField(default=0)),
                ("locked_until", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "account",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="credential",
                        to="authentication.account",
                    ),
                ),
            ],
            options={
                "db_table": "credentials",
                "indexes": [
                    models.Index(fields=["locked_until"], name="idx_credentials_locked_until")
                ],
            },
        ),
        migrations.CreateModel(
            name="LoginAuditLog",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("email_attempted", models.EmailField(blank=True, max_length=254, null=True)),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("login_success", "Login success"),
                            ("login_failure", "Login failure"),
                            ("logout", "Logout"),
                            ("token_refresh", "Token refresh"),
                            ("password_reset", "Password reset"),
                        ],
                        max_length=40,
                    ),
                ),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True, null=True)),
                ("metadata", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "account",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="login_audit_logs",
                        to="authentication.account",
                    ),
                ),
            ],
            options={
                "db_table": "login_audit_logs",
                "indexes": [
                    models.Index(
                        fields=["account", "created_at"], name="idx_login_audit_account_ts"
                    ),
                    models.Index(fields=["event_type"], name="idx_login_audit_event_type"),
                    models.Index(fields=["email_attempted"], name="idx_login_audit_email"),
                ],
            },
        ),
        migrations.CreateModel(
            name="RefreshToken",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("token_jti", models.UUIDField(unique=True)),
                ("token_hash", models.TextField()),
                ("issued_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("expires_at", models.DateTimeField()),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("device_label", models.CharField(blank=True, max_length=128, null=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True, null=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="refresh_tokens",
                        to="authentication.account",
                    ),
                ),
            ],
            options={
                "db_table": "refresh_tokens",
                "indexes": [
                    models.Index(fields=["account"], name="idx_refresh_tokens_account_id"),
                    models.Index(fields=["expires_at"], name="idx_refresh_tokens_expires_at"),
                ],
            },
        ),
        migrations.CreateModel(
            name="TokenBlacklist",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("token_jti", models.UUIDField(unique=True)),
                (
                    "reason",
                    models.CharField(
                        choices=[
                            ("logout", "Logout"),
                            ("rotation", "Rotation"),
                            ("admin_revoke", "Admin revoke"),
                            ("password_change", "Password change"),
                            ("compromised", "Compromised"),
                        ],
                        default="logout",
                        max_length=64,
                    ),
                ),
                ("expires_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "account",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="blacklisted_tokens",
                        to="authentication.account",
                    ),
                ),
            ],
            options={
                "db_table": "token_blacklist",
                "indexes": [
                    models.Index(fields=["expires_at"], name="idx_token_blacklist_expires_at")
                ],
            },
        ),
    ]
