# Generated for LearnGrid LMS T-021 Redis architecture.

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0002_rbac_authorization"),
    ]

    operations = [
        migrations.CreateModel(
            name="PasswordResetToken",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("token_hash", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("used", "Used"),
                            ("expired", "Expired"),
                            ("revoked", "Revoked"),
                        ],
                        default="pending",
                        max_length=24,
                    ),
                ),
                ("requested_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("expires_at", models.DateTimeField()),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="password_reset_tokens",
                        to="authentication.account",
                    ),
                ),
            ],
            options={
                "db_table": "password_reset_tokens",
                "indexes": [
                    models.Index(fields=["account"], name="idx_password_reset_account_id"),
                    models.Index(
                        fields=["status", "expires_at"], name="idx_password_reset_status_exp"
                    ),
                ],
            },
        ),
    ]
