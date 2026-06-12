# Generated for LearnGrid LMS T-003 RBAC and object authorization.

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


ROLE_DEFINITIONS = [
    ("super_admin", "Super Admin", "platform"),
    ("institution_admin", "Institution Admin", "institution"),
    ("instructor", "Instructor", "course"),
    ("teaching_assistant", "Teaching Assistant", "course"),
    ("student", "Student", "course"),
    ("parent_guardian", "Parent or Guardian", "institution"),
]

PERMISSION_DEFINITIONS = [
    ("rbac.manage", "rbac", "manage", "Manage roles, permissions, and assignments."),
    ("institution.manage", "institution", "manage", "Manage institution records."),
    ("profile.view", "profile", "view", "View profile records."),
    ("profile.manage", "profile", "manage", "Manage profile records."),
    ("course.view", "course", "view", "View course records."),
    ("course.manage", "course", "manage", "Manage course records."),
    ("content.view", "content", "view", "View content assets."),
    ("content.manage", "content", "manage", "Manage content assets."),
    ("enrollment.view", "enrollment", "view", "View enrollments."),
    ("enrollment.manage", "enrollment", "manage", "Manage enrollments."),
    ("progress.view", "progress", "view", "View learner progress."),
    ("progress.manage", "progress", "manage", "Manage learner progress."),
    ("assessment.view", "assessment", "view", "View assessments."),
    ("assessment.manage", "assessment", "manage", "Manage assessments."),
    ("submission.view", "submission", "view", "View submissions."),
    ("submission.manage", "submission", "manage", "Manage submissions."),
    ("grade.view", "grade", "view", "View grades."),
    ("grade.manage", "grade", "manage", "Manage grades."),
    ("notification.view", "notification", "view", "View notifications."),
    ("notification.manage", "notification", "manage", "Manage notifications."),
    ("analytics.view", "analytics", "view", "View analytics."),
]

ROLE_PERMISSION_MAP = {
    "super_admin": [permission[0] for permission in PERMISSION_DEFINITIONS],
    "institution_admin": [
        "institution.manage",
        "profile.view",
        "profile.manage",
        "course.view",
        "course.manage",
        "content.view",
        "content.manage",
        "enrollment.view",
        "enrollment.manage",
        "progress.view",
        "progress.manage",
        "assessment.view",
        "assessment.manage",
        "submission.view",
        "submission.manage",
        "grade.view",
        "grade.manage",
        "notification.view",
        "notification.manage",
        "analytics.view",
    ],
    "instructor": [
        "profile.view",
        "course.view",
        "course.manage",
        "content.view",
        "content.manage",
        "enrollment.view",
        "progress.view",
        "progress.manage",
        "assessment.view",
        "assessment.manage",
        "submission.view",
        "submission.manage",
        "grade.view",
        "grade.manage",
        "notification.view",
        "analytics.view",
    ],
    "teaching_assistant": [
        "profile.view",
        "course.view",
        "content.view",
        "enrollment.view",
        "progress.view",
        "assessment.view",
        "submission.view",
        "submission.manage",
        "grade.view",
        "notification.view",
    ],
    "student": [
        "profile.view",
        "course.view",
        "content.view",
        "enrollment.view",
        "progress.view",
        "progress.manage",
        "assessment.view",
        "submission.view",
        "submission.manage",
        "grade.view",
        "notification.view",
    ],
    "parent_guardian": [
        "profile.view",
        "progress.view",
        "grade.view",
        "notification.view",
    ],
}


def seed_rbac(apps, _schema_editor):
    role_model = apps.get_model("authentication", "Role")
    permission_model = apps.get_model("authentication", "Permission")
    role_permission_model = apps.get_model("authentication", "RolePermission")

    roles = {}
    for code, name, scope_type in ROLE_DEFINITIONS:
        role, _created = role_model.objects.update_or_create(
            code=code,
            defaults={"name": name, "scope_type": scope_type, "is_system": True},
        )
        roles[code] = role

    permissions = {}
    for code, resource, action, description in PERMISSION_DEFINITIONS:
        permission, _created = permission_model.objects.update_or_create(
            code=code,
            defaults={"resource": resource, "action": action, "description": description},
        )
        permissions[code] = permission

    for role_code, permission_codes in ROLE_PERMISSION_MAP.items():
        for permission_code in permission_codes:
            role_permission_model.objects.get_or_create(
                role=roles[role_code],
                permission=permissions[permission_code],
            )


def unseed_rbac(_apps, _schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Permission",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("code", models.CharField(max_length=128, unique=True)),
                ("resource", models.CharField(max_length=64)),
                ("action", models.CharField(max_length=64)),
                ("description", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "permissions",
                "indexes": [
                    models.Index(fields=["resource", "action"], name="idx_perm_resource_action")
                ],
            },
        ),
        migrations.CreateModel(
            name="Role",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("code", models.CharField(max_length=64, unique=True)),
                ("name", models.CharField(max_length=128)),
                (
                    "scope_type",
                    models.CharField(
                        choices=[
                            ("platform", "Platform"),
                            ("institution", "Institution"),
                            ("course", "Course"),
                        ],
                        default="institution",
                        max_length=32,
                    ),
                ),
                ("is_system", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "roles",
                "indexes": [models.Index(fields=["scope_type"], name="idx_roles_scope_type")],
            },
        ),
        migrations.CreateModel(
            name="RoleAssignment",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "scope_type",
                    models.CharField(
                        choices=[
                            ("platform", "Platform"),
                            ("institution", "Institution"),
                            ("course", "Course"),
                            ("assessment", "Assessment"),
                        ],
                        default="platform",
                        max_length=32,
                    ),
                ),
                ("scope_id", models.UUIDField(blank=True, null=True)),
                ("assigned_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="role_assignments",
                        to="authentication.account",
                    ),
                ),
                (
                    "assigned_by_account",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_role_assignments",
                        to="authentication.account",
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="role_assignments",
                        to="authentication.role",
                    ),
                ),
            ],
            options={
                "db_table": "role_assignments",
                "indexes": [
                    models.Index(fields=["account"], name="idx_role_assign_account"),
                    models.Index(fields=["scope_type", "scope_id"], name="idx_role_assign_scope"),
                ],
            },
        ),
        migrations.CreateModel(
            name="RolePermission",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "permission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="role_permissions",
                        to="authentication.permission",
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="role_permissions",
                        to="authentication.role",
                    ),
                ),
            ],
            options={
                "db_table": "role_permissions",
                "indexes": [models.Index(fields=["permission"], name="idx_role_perm_permission")],
            },
        ),
        migrations.CreateModel(
            name="AuthorizationAuditLog",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("role_assignment_created", "Role assignment created"),
                            ("role_assignment_revoked", "Role assignment revoked"),
                            ("role_permission_granted", "Role permission granted"),
                            ("role_permission_revoked", "Role permission revoked"),
                        ],
                        max_length=64,
                    ),
                ),
                ("scope_type", models.CharField(blank=True, max_length=32)),
                ("scope_id", models.UUIDField(blank=True, null=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True, null=True)),
                ("metadata", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor_account",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="authorization_audit_actions",
                        to="authentication.account",
                    ),
                ),
                (
                    "permission",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="authentication.permission",
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="authentication.role",
                    ),
                ),
                (
                    "role_assignment",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="authentication.roleassignment",
                    ),
                ),
                (
                    "target_account",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="authorization_audit_targets",
                        to="authentication.account",
                    ),
                ),
            ],
            options={
                "db_table": "authorization_audit_logs",
                "indexes": [
                    models.Index(
                        fields=["actor_account", "created_at"], name="idx_auth_audit_actor_created"
                    ),
                    models.Index(fields=["target_account"], name="idx_auth_audit_target"),
                    models.Index(fields=["event_type"], name="idx_auth_audit_event_type"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="roleassignment",
            constraint=models.UniqueConstraint(
                condition=models.Q(("revoked_at__isnull", True), ("scope_id__isnull", True)),
                fields=("account", "role", "scope_type"),
                name="uq_active_role_assign_platform",
            ),
        ),
        migrations.AddConstraint(
            model_name="roleassignment",
            constraint=models.UniqueConstraint(
                condition=models.Q(("revoked_at__isnull", True), ("scope_id__isnull", False)),
                fields=("account", "role", "scope_type", "scope_id"),
                name="uq_active_role_assign_scoped",
            ),
        ),
        migrations.AddConstraint(
            model_name="rolepermission",
            constraint=models.UniqueConstraint(
                fields=("role", "permission"),
                name="uq_role_perm_role_permission",
            ),
        ),
        migrations.RunPython(seed_rbac, unseed_rbac),
    ]
