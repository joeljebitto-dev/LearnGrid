from __future__ import annotations

import hmac
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Any

import jwt
import redis
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

from .models import (
    Account,
    AccountStatus,
    AssignmentScopeType,
    AuthorizationAuditEvent,
    AuthorizationAuditLog,
    BlacklistReason,
    Credential,
    LoginAuditEvent,
    LoginAuditLog,
    Permission,
    Role,
    RoleAssignment,
    RolePermission,
    RefreshToken,
    TokenBlacklist,
)


_UNSET = object()


@dataclass(frozen=True)
class TokenPair:
    access: str
    refresh: str
    access_expires_at: datetime
    refresh_expires_at: datetime

    def as_response(self) -> dict[str, str]:
        return {
            "access": self.access,
            "refresh": self.refresh,
            "access_expires_at": self.access_expires_at.isoformat(),
            "refresh_expires_at": self.refresh_expires_at.isoformat(),
        }


def _epoch_seconds(value: datetime | None) -> int:
    if value is None:
        return 0
    return int(value.timestamp())


def _password_stamp(value: datetime | None) -> int:
    if value is None:
        return 0
    return int(value.timestamp() * 1000)


def hash_token(token: str) -> str:
    return hmac.new(
        settings.AUTH_TOKEN_HASH_KEY.encode("utf-8"),
        token.encode("utf-8"),
        sha256,
    ).hexdigest()


def _redis_client() -> redis.Redis:
    return redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=0.2,
        socket_timeout=0.2,
    )


def _blacklist_key(token_jti: uuid.UUID | str) -> str:
    return f"auth:blacklist:{token_jti}"


def _ttl_seconds(expires_at: timezone.datetime) -> int:
    return max(0, int((expires_at - timezone.now()).total_seconds()))


def _request_ip(request: Any) -> str | None:
    if request is None:
        return None
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.META.get("REMOTE_ADDR")


def _request_user_agent(request: Any) -> str | None:
    if request is None:
        return None
    return request.META.get("HTTP_USER_AGENT")


def _audit(
    event_type: str,
    account: Account | None = None,
    email_attempted: str | None = None,
    request: Any = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    LoginAuditLog.objects.create(
        account=account,
        email_attempted=email_attempted,
        event_type=event_type,
        ip_address=_request_ip(request),
        user_agent=_request_user_agent(request),
        metadata=metadata or {},
    )


def encode_token(
    *,
    account: Account,
    credential: Credential,
    token_type: str,
    token_jti: uuid.UUID,
    expires_at: timezone.datetime,
) -> str:
    now = timezone.now()
    payload = {
        "iss": settings.AUTH_JWT_ISSUER,
        "sub": str(account.id),
        "typ": token_type,
        "jti": str(token_jti),
        "iat": _epoch_seconds(now),
        "exp": _epoch_seconds(expires_at),
        "pwd_changed_at": _password_stamp(credential.password_changed_at),
    }
    return jwt.encode(payload, settings.AUTH_JWT_SIGNING_KEY, algorithm=settings.AUTH_JWT_ALGORITHM)


def decode_token(token: str, expected_type: str, *, verify_exp: bool = True) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.AUTH_JWT_SIGNING_KEY,
            algorithms=[settings.AUTH_JWT_ALGORITHM],
            issuer=settings.AUTH_JWT_ISSUER,
            options={"verify_exp": verify_exp},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationFailed("Token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationFailed("Token is invalid.") from exc

    if payload.get("typ") != expected_type:
        raise AuthenticationFailed("Token type is invalid.")
    return payload


def blacklist_token_jti(
    token_jti: uuid.UUID | str,
    expires_at: timezone.datetime,
    *,
    account: Account | None = None,
    reason: str = BlacklistReason.LOGOUT,
) -> None:
    token_uuid = uuid.UUID(str(token_jti))
    TokenBlacklist.objects.update_or_create(
        token_jti=token_uuid,
        defaults={"account": account, "reason": reason, "expires_at": expires_at},
    )

    ttl = _ttl_seconds(expires_at)
    if ttl <= 0:
        return

    try:
        _redis_client().setex(_blacklist_key(token_uuid), ttl, "1")
    except redis.RedisError:
        return


def is_token_blacklisted(token_jti: uuid.UUID | str) -> bool:
    token_uuid = uuid.UUID(str(token_jti))
    try:
        return bool(_redis_client().exists(_blacklist_key(token_uuid)))
    except redis.RedisError:
        return TokenBlacklist.objects.filter(
            token_jti=token_uuid,
            expires_at__gt=timezone.now(),
        ).exists()


def _get_active_account(account_id: str) -> Account:
    try:
        account = Account.objects.select_related("credential").get(id=account_id)
    except Account.DoesNotExist as exc:
        raise AuthenticationFailed("Account was not found.") from exc

    if not account.is_active:
        raise AuthenticationFailed("Account is not active.")
    return account


def _validate_password_changed_claim(payload: dict[str, Any], credential: Credential) -> None:
    token_password_changed = int(payload.get("pwd_changed_at", 0))
    if token_password_changed < _password_stamp(credential.password_changed_at):
        raise AuthenticationFailed("Token has been invalidated.")


def issue_token_pair(
    account: Account,
    *,
    request: Any = None,
    device_label: str | None = None,
) -> TokenPair:
    credential = account.credential
    now = timezone.now()
    access_expires_at = now + timedelta(seconds=settings.AUTH_ACCESS_TOKEN_LIFETIME_SECONDS)
    refresh_expires_at = now + timedelta(seconds=settings.AUTH_REFRESH_TOKEN_LIFETIME_SECONDS)
    access_jti = uuid.uuid4()
    refresh_jti = uuid.uuid4()

    access = encode_token(
        account=account,
        credential=credential,
        token_type="access",
        token_jti=access_jti,
        expires_at=access_expires_at,
    )
    refresh = encode_token(
        account=account,
        credential=credential,
        token_type="refresh",
        token_jti=refresh_jti,
        expires_at=refresh_expires_at,
    )
    RefreshToken.objects.create(
        account=account,
        token_jti=refresh_jti,
        token_hash=hash_token(refresh),
        issued_at=now,
        expires_at=refresh_expires_at,
        device_label=device_label,
        ip_address=_request_ip(request),
        user_agent=_request_user_agent(request),
    )
    return TokenPair(access, refresh, access_expires_at, refresh_expires_at)


@transaction.atomic
def issue_token_pair_for_credentials(
    *,
    email: str,
    password: str,
    request: Any = None,
    device_label: str | None = None,
) -> TokenPair:
    normalized_email = email.strip().lower()
    try:
        account = Account.objects.select_related("credential").get(email__iexact=normalized_email)
    except Account.DoesNotExist as exc:
        _audit(LoginAuditEvent.LOGIN_FAILURE, email_attempted=normalized_email, request=request)
        raise AuthenticationFailed("Invalid email or password.") from exc

    if not account.is_active or not check_password(password, account.credential.password_hash):
        _audit(
            LoginAuditEvent.LOGIN_FAILURE,
            account=account,
            email_attempted=normalized_email,
            request=request,
        )
        raise AuthenticationFailed("Invalid email or password.")

    account.last_login_at = timezone.now()
    account.save(update_fields=["last_login_at", "updated_at"])
    _audit(LoginAuditEvent.LOGIN_SUCCESS, account=account, request=request)
    return issue_token_pair(account, request=request, device_label=device_label)


@transaction.atomic
def create_managed_account(
    *,
    email: str,
    temporary_password: str,
    phone: str | None = None,
    role_code: str | None = None,
    scope_type: str = AssignmentScopeType.PLATFORM,
    scope_id: uuid.UUID | str | None = None,
    actor_account: Account | None = None,
    request: Any = None,
) -> Account:
    account = Account.objects.create(
        email=email.strip().lower(),
        phone=phone or None,
        status=AccountStatus.ACTIVE,
    )
    Credential.objects.create(
        account=account,
        password_hash=make_password(temporary_password),
        must_change_password=True,
    )
    if role_code:
        role = Role.objects.get(code=role_code)
        assign_role(
            account=account,
            role=role,
            scope_type=scope_type,
            scope_id=scope_id,
            assigned_by_account=actor_account,
            request=request,
        )
    return account


@transaction.atomic
def update_managed_account(
    account: Account,
    *,
    email=_UNSET,
    phone=_UNSET,
    status=_UNSET,
) -> Account:
    update_fields = ["updated_at"]
    revoke_tokens = False
    if email is not _UNSET:
        account.email = email.strip().lower()
        update_fields.append("email")
    if phone is not _UNSET:
        account.phone = phone or None
        update_fields.append("phone")
    if status is not _UNSET:
        account.status = status
        update_fields.append("status")
        if status == AccountStatus.DEACTIVATED:
            account.deleted_at = timezone.now()
            update_fields.append("deleted_at")
            revoke_tokens = True
    account.save(update_fields=update_fields)
    if revoke_tokens:
        revoke_account_tokens(account, reason=BlacklistReason.ADMIN_REVOKE)
    return account


@transaction.atomic
def deactivate_managed_account(account: Account) -> Account:
    account.status = AccountStatus.DEACTIVATED
    account.deleted_at = timezone.now()
    account.save(update_fields=["status", "deleted_at", "updated_at"])
    revoke_account_tokens(account, reason=BlacklistReason.ADMIN_REVOKE)
    return account


@transaction.atomic
def refresh_token_pair(refresh_token: str, *, request: Any = None) -> TokenPair:
    payload = decode_token(refresh_token, "refresh")
    token_jti = uuid.UUID(str(payload["jti"]))
    if is_token_blacklisted(token_jti):
        raise AuthenticationFailed("Refresh token has been revoked.")

    account = _get_active_account(str(payload["sub"]))
    _validate_password_changed_claim(payload, account.credential)

    try:
        stored_token = RefreshToken.objects.select_for_update().get(
            token_jti=token_jti,
            token_hash=hash_token(refresh_token),
            account=account,
        )
    except RefreshToken.DoesNotExist as exc:
        raise AuthenticationFailed("Refresh token is invalid.") from exc

    if not stored_token.is_active:
        raise AuthenticationFailed("Refresh token has expired or been revoked.")

    now = timezone.now()
    stored_token.revoked_at = now
    stored_token.save(update_fields=["revoked_at"])
    blacklist_token_jti(
        token_jti,
        stored_token.expires_at,
        account=account,
        reason=BlacklistReason.ROTATION,
    )
    _audit(LoginAuditEvent.TOKEN_REFRESH, account=account, request=request)
    return issue_token_pair(account, request=request, device_label=stored_token.device_label)


@transaction.atomic
def logout_tokens(
    *,
    refresh_token: str,
    access_token: str | None = None,
    request: Any = None,
) -> None:
    payload = decode_token(refresh_token, "refresh", verify_exp=False)
    account = _get_active_account(str(payload["sub"]))
    token_jti = uuid.UUID(str(payload["jti"]))
    refresh_expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.get_current_timezone())

    RefreshToken.objects.filter(
        token_jti=token_jti,
        token_hash=hash_token(refresh_token),
        account=account,
        revoked_at__isnull=True,
    ).update(revoked_at=timezone.now())
    blacklist_token_jti(token_jti, refresh_expires_at, account=account, reason=BlacklistReason.LOGOUT)

    if access_token:
        access_payload = decode_token(access_token, "access", verify_exp=False)
        access_jti = uuid.UUID(str(access_payload["jti"]))
        access_expires_at = datetime.fromtimestamp(
            access_payload["exp"],
            tz=timezone.get_current_timezone(),
        )
        blacklist_token_jti(
            access_jti,
            access_expires_at,
            account=account,
            reason=BlacklistReason.LOGOUT,
        )

    _audit(LoginAuditEvent.LOGOUT, account=account, request=request)


def authenticate_access_token(access_token: str) -> Account:
    payload = decode_token(access_token, "access")
    token_jti = uuid.UUID(str(payload["jti"]))
    if is_token_blacklisted(token_jti):
        raise AuthenticationFailed("Access token has been revoked.")

    account = _get_active_account(str(payload["sub"]))
    _validate_password_changed_claim(payload, account.credential)
    return account


@transaction.atomic
def revoke_account_tokens(
    account: Account,
    *,
    reason: str = BlacklistReason.ADMIN_REVOKE,
) -> None:
    now = timezone.now()
    Credential.objects.filter(account=account).update(password_changed_at=now)
    for token in RefreshToken.objects.select_for_update().filter(
        account=account,
        revoked_at__isnull=True,
        expires_at__gt=now,
    ):
        token.revoked_at = now
        token.save(update_fields=["revoked_at"])
        blacklist_token_jti(token.token_jti, token.expires_at, account=account, reason=reason)


def _permission_cache_key(
    account_id: uuid.UUID | str,
    permission_code: str,
    scope_type: str,
    scope_id: uuid.UUID | str | None,
) -> str:
    normalized_scope = str(scope_id) if scope_id else "none"
    return f"auth:permissions:{account_id}:{permission_code}:{scope_type}:{normalized_scope}"


def _permission_cache_prefix(account_id: uuid.UUID | str | None = None) -> str:
    if account_id:
        return f"auth:permissions:{account_id}:"
    return "auth:permissions:"


def _normalize_scope_id(scope_type: str, scope_id: uuid.UUID | str | None) -> uuid.UUID | None:
    if scope_type == AssignmentScopeType.PLATFORM:
        return None
    if scope_id is None or scope_id == "":
        raise ValueError("scope_id is required for scoped authorization.")
    return uuid.UUID(str(scope_id))


def _validate_scope(scope_type: str, scope_id: uuid.UUID | str | None) -> uuid.UUID | None:
    if scope_type not in AssignmentScopeType.values:
        raise ValueError("scope_type is invalid.")
    return _normalize_scope_id(scope_type, scope_id)


def _audit_authorization(
    event_type: str,
    *,
    actor_account: Account | None = None,
    target_account: Account | None = None,
    role: Role | None = None,
    permission: Permission | None = None,
    role_assignment: RoleAssignment | None = None,
    scope_type: str = "",
    scope_id: uuid.UUID | None = None,
    request: Any = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    AuthorizationAuditLog.objects.create(
        actor_account=actor_account,
        target_account=target_account,
        event_type=event_type,
        role=role,
        permission=permission,
        role_assignment=role_assignment,
        scope_type=scope_type,
        scope_id=scope_id,
        ip_address=_request_ip(request),
        user_agent=_request_user_agent(request),
        metadata=metadata or {},
    )


def invalidate_permission_cache(account_id: uuid.UUID | str | None = None) -> None:
    prefix = _permission_cache_prefix(account_id)
    try:
        client = _redis_client()
        keys = list(client.scan_iter(f"{prefix}*"))
        if keys:
            client.delete(*keys)
    except redis.RedisError:
        return


def has_active_role(
    account: Account,
    role_code: str,
    *,
    scope_type: str | None = None,
    scope_id: uuid.UUID | str | None = None,
) -> bool:
    if not account.is_active:
        return False

    assignments = RoleAssignment.objects.filter(
        account=account,
        role__code=role_code,
        revoked_at__isnull=True,
    )
    if scope_type is not None:
        normalized_scope_id = _validate_scope(scope_type, scope_id)
        assignments = assignments.filter(scope_type=scope_type, scope_id=normalized_scope_id)
    return assignments.exists()


def _has_super_admin_role(account: Account) -> bool:
    return has_active_role(account, "super_admin")


def _permission_exists(permission_code: str) -> bool:
    return Permission.objects.filter(code=permission_code).exists()


def _has_permission_from_database(
    account: Account,
    permission_code: str,
    scope_type: str,
    scope_id: uuid.UUID | None,
) -> bool:
    if not account.is_active or not _permission_exists(permission_code):
        return False

    if _has_super_admin_role(account):
        return True

    scope_filter = Q(scope_type=AssignmentScopeType.PLATFORM, scope_id__isnull=True)
    if scope_type != AssignmentScopeType.PLATFORM:
        scope_filter |= Q(scope_type=scope_type, scope_id=scope_id)

    return RoleAssignment.objects.filter(
        scope_filter,
        account=account,
        revoked_at__isnull=True,
        role__role_permissions__permission__code=permission_code,
    ).exists()


def has_permission(
    account: Account,
    permission_code: str,
    *,
    scope_type: str = AssignmentScopeType.PLATFORM,
    scope_id: uuid.UUID | str | None = None,
) -> bool:
    normalized_scope_id = _validate_scope(scope_type, scope_id)
    cache_key = _permission_cache_key(account.id, permission_code, scope_type, normalized_scope_id)

    try:
        cached = _redis_client().get(cache_key)
        if cached is not None:
            return cached == "1"
    except redis.RedisError:
        return _has_permission_from_database(account, permission_code, scope_type, normalized_scope_id)

    allowed = _has_permission_from_database(account, permission_code, scope_type, normalized_scope_id)
    try:
        _redis_client().setex(
            cache_key,
            settings.AUTH_PERMISSION_CACHE_TTL_SECONDS,
            "1" if allowed else "0",
        )
    except redis.RedisError:
        pass
    return allowed


def require_permission(
    account: Account,
    permission_code: str,
    *,
    scope_type: str = AssignmentScopeType.PLATFORM,
    scope_id: uuid.UUID | str | None = None,
) -> None:
    if not has_permission(account, permission_code, scope_type=scope_type, scope_id=scope_id):
        raise PermissionDenied("You do not have permission to perform this action.")


def assign_role(
    *,
    account: Account,
    role: Role,
    scope_type: str,
    scope_id: uuid.UUID | str | None = None,
    assigned_by_account: Account | None = None,
    request: Any = None,
) -> RoleAssignment:
    normalized_scope_id = _validate_scope(scope_type, scope_id)
    assignment, created = RoleAssignment.objects.update_or_create(
        account=account,
        role=role,
        scope_type=scope_type,
        scope_id=normalized_scope_id,
        revoked_at__isnull=True,
        defaults={"assigned_by_account": assigned_by_account, "assigned_at": timezone.now()},
    )
    _audit_authorization(
        AuthorizationAuditEvent.ROLE_ASSIGNMENT_CREATED,
        actor_account=assigned_by_account,
        target_account=account,
        role=role,
        role_assignment=assignment,
        scope_type=scope_type,
        scope_id=normalized_scope_id,
        request=request,
        metadata={"created": created},
    )
    invalidate_permission_cache(account.id)
    return assignment


def revoke_role_assignment(
    assignment: RoleAssignment,
    *,
    revoked_by_account: Account | None = None,
    request: Any = None,
) -> RoleAssignment:
    if assignment.revoked_at is None:
        assignment.revoked_at = timezone.now()
        assignment.save(update_fields=["revoked_at"])

    _audit_authorization(
        AuthorizationAuditEvent.ROLE_ASSIGNMENT_REVOKED,
        actor_account=revoked_by_account,
        target_account=assignment.account,
        role=assignment.role,
        role_assignment=assignment,
        scope_type=assignment.scope_type,
        scope_id=assignment.scope_id,
        request=request,
    )
    invalidate_permission_cache(assignment.account_id)
    return assignment


def grant_role_permission(
    *,
    role: Role,
    permission: Permission,
    actor_account: Account | None = None,
    request: Any = None,
) -> RolePermission:
    role_permission, created = RolePermission.objects.get_or_create(role=role, permission=permission)
    if created:
        _audit_authorization(
            AuthorizationAuditEvent.ROLE_PERMISSION_GRANTED,
            actor_account=actor_account,
            role=role,
            permission=permission,
            request=request,
        )
        invalidate_permission_cache()
    return role_permission


def revoke_role_permission(
    *,
    role: Role,
    permission: Permission,
    actor_account: Account | None = None,
    request: Any = None,
) -> None:
    deleted, _ = RolePermission.objects.filter(role=role, permission=permission).delete()
    if deleted:
        _audit_authorization(
            AuthorizationAuditEvent.ROLE_PERMISSION_REVOKED,
            actor_account=actor_account,
            role=role,
            permission=permission,
            request=request,
        )
        invalidate_permission_cache()
