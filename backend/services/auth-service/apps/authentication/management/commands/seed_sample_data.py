from __future__ import annotations

import sys
from pathlib import Path

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

ROOT = Path(__file__).resolve().parents[7]
sys.path.append(str(ROOT / "scripts" / "sample_data"))

from seed_helpers import (  # noqa: E402
    account_id,
    add_seed_arguments,
    course_id,
    institution_id,
    load_manifest,
    now,
    planned,
    seed_metadata,
    uuid_value,
)

from apps.authentication.models import (  # noqa: E402
    Account,
    AccountStatus,
    AssignmentScopeType,
    AuthorizationAuditEvent,
    AuthorizationAuditLog,
    Credential,
    LoginAuditEvent,
    LoginAuditLog,
    Role,
    RoleAssignment,
)


class Command(BaseCommand):
    help = "Seed LearnGrid demo sample data for auth-service."

    def add_arguments(self, parser) -> None:
        add_seed_arguments(parser, __file__)

    def handle(self, *args, **options) -> None:
        manifest = load_manifest(options["manifest"])
        records = [
            "accounts",
            "credentials",
            "role_assignments",
            "login_audit_logs",
            "authorization_audit_logs",
        ]

        if options["dry_run"]:
            planned(self, "auth-service", manifest, records)
            return

        with transaction.atomic():
            if options["reset_sample_data"]:
                self.reset(manifest)
            self.seed(manifest)

        self.stdout.write(self.style.SUCCESS("Seeded auth-service sample data."))

    def reset(self, manifest: dict) -> None:
        account_ids = [account_id(manifest, key) for key in manifest["accounts"]]
        emails = [account["email"] for account in manifest["accounts"].values()]
        RoleAssignment.objects.filter(account_id__in=account_ids).delete()
        Credential.objects.filter(account_id__in=account_ids).delete()
        LoginAuditLog.objects.filter(metadata__seed_namespace=manifest["seed_namespace"]).delete()
        AuthorizationAuditLog.objects.filter(
            metadata__seed_namespace=manifest["seed_namespace"]
        ).delete()
        Account.objects.filter(id__in=account_ids).delete()
        Account.objects.filter(email__in=emails).delete()

    def seed(self, manifest: dict) -> None:
        accounts: dict[str, Account] = {}
        for key, account_data in manifest["accounts"].items():
            desired_id = uuid_value(account_data["id"])
            Account.objects.filter(email=account_data["email"]).exclude(id=desired_id).delete()
            account, _created = Account.objects.update_or_create(
                id=desired_id,
                defaults={
                    "email": account_data["email"],
                    "phone": None,
                    "status": AccountStatus.ACTIVE,
                    "is_staff": key in {"super_admin", "institution_admin"},
                    "deleted_at": None,
                },
            )
            Credential.objects.update_or_create(
                account=account,
                defaults={
                    "password_hash": make_password(account_data["password"]),
                    "must_change_password": False,
                    "failed_attempt_count": 0,
                    "locked_until": None,
                    "password_changed_at": now(),
                },
            )
            accounts[key] = account

        roles = {}
        for account_data in manifest["accounts"].values():
            role_code = account_data["role"]
            try:
                roles[role_code] = Role.objects.get(code=role_code)
            except Role.DoesNotExist as exc:
                raise CommandError(
                    f"Missing RBAC role {role_code!r}. Run auth-service migrations first."
                ) from exc

        scope_map = {
            "super_admin": (AssignmentScopeType.PLATFORM, None),
            "institution_admin": (AssignmentScopeType.INSTITUTION, institution_id(manifest)),
            "instructor": (AssignmentScopeType.COURSE, course_id(manifest)),
            "student": (AssignmentScopeType.INSTITUTION, institution_id(manifest)),
        }

        for key, account in accounts.items():
            role = roles[manifest["accounts"][key]["role"]]
            scope_type, scope_id = scope_map[key]
            RoleAssignment.objects.update_or_create(
                account=account,
                role=role,
                scope_type=scope_type,
                scope_id=scope_id,
                revoked_at__isnull=True,
                defaults={
                    "assigned_by_account": accounts["super_admin"],
                    "assigned_at": now(),
                    "revoked_at": None,
                },
            )

        LoginAuditLog.objects.filter(metadata__seed_namespace=manifest["seed_namespace"]).delete()
        AuthorizationAuditLog.objects.filter(
            metadata__seed_namespace=manifest["seed_namespace"]
        ).delete()
        for key, account in accounts.items():
            LoginAuditLog.objects.create(
                account=account,
                email_attempted=account.email,
                event_type=LoginAuditEvent.LOGIN_SUCCESS,
                metadata=seed_metadata(f"{key}-login-audit"),
            )
            role = roles[manifest["accounts"][key]["role"]]
            AuthorizationAuditLog.objects.create(
                actor_account=accounts["super_admin"],
                target_account=account,
                event_type=AuthorizationAuditEvent.ROLE_ASSIGNMENT_CREATED,
                role=role,
                scope_type=scope_map[key][0],
                scope_id=scope_map[key][1],
                metadata=seed_metadata(f"{key}-role-assignment-audit"),
            )

