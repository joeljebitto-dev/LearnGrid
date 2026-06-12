from __future__ import annotations

import hmac
import json
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Any, cast

import jwt
import redis
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from learngrid_redis import RedisKeyBuilder
from learngrid_redis import digest_json
from learngrid_redis import digest_value
from learngrid_redis import fixed_window_rate_limit
from learngrid_redis import redis_client
from learngrid_redis import set_json_cache
from learngrid_events import publish_event as publish_kafka_event
from rest_framework.exceptions import APIException, AuthenticationFailed
from rest_framework.exceptions import PermissionDenied, Throttled
from rest_framework.exceptions import ValidationError

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
    PasswordResetStatus,
    PasswordResetToken,
    Role,
    RoleAssignment,
    RolePermission,
    RefreshToken,
    TokenBlacklist,
)


_UNSET = object()
AUTH_ACCOUNT_CREATED_AUDIT_EVENT = "auth_account_created"
AUTH_ACCOUNT_UPDATED_AUDIT_EVENT = "auth_account_updated"
AUTH_ACCOUNT_DEACTIVATED_AUDIT_EVENT = "auth_account_deactivated"


class RedisSecurityUnavailable(APIException):
    status_code = 503
    default_code = "redis_security_unavailable"
    default_detail = "Security controls are temporarily unavailable."


def _validate_password_policy(password: str, *, field_name: str) -> None:
    try:
        validate_password(password)
    except DjangoValidationError as exc:
        raise ValidationError({field_name: list(exc.messages)}) from exc


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
    return redis_client(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT_SECONDS,
    )


def _key_builder() -> RedisKeyBuilder:
    return RedisKeyBuilder(service=settings.SERVICE_NAME, env=settings.REDIS_ENV)


def _blacklist_key(token_jti: uuid.UUID | str) -> str:
    return _key_builder().key("blacklist", "jwt", str(token_jti))


def _password_reset_key(raw_token: str) -> str:
    return _key_builder().key("password-reset", "token", digest_value(raw_token))


def _otp_key(*, purpose: str, subject: str) -> str:
    return _key_builder().key(
        "otp",
        purpose,
        digest_json({"purpose": purpose, "subject": subject}),
    )


def _ttl_seconds(expires_at: datetime) -> int:
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


def _enforce_rate_limit(
    *,
    name: str,
    identity: dict[str, Any],
    limit: int,
    window_seconds: int,
    detail: str,
) -> None:
    key = _key_builder().key("rate-limit", name, digest_json(identity))
    try:
        result = fixed_window_rate_limit(
            _redis_client(),
            key,
            limit=limit,
            window_seconds=window_seconds,
        )
    except RuntimeError as exc:
        raise Throttled(
            detail="Redis-backed rate limiting is temporarily unavailable.",
            wait=window_seconds,
        ) from exc
    if not result.allowed:
        raise Throttled(detail=detail, wait=result.ttl_seconds or window_seconds)


def _enforce_login_rate_limit(*, email: str, request: Any = None) -> None:
    _enforce_rate_limit(
        name="login",
        identity={"email": email, "ip": _request_ip(request)},
        limit=settings.AUTH_LOGIN_RATE_LIMIT_COUNT,
        window_seconds=settings.AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS,
        detail="Too many login attempts.",
    )


def _enforce_password_reset_rate_limit(*, email: str, request: Any = None) -> None:
    _enforce_rate_limit(
        name="password-reset",
        identity={"email": email, "ip": _request_ip(request)},
        limit=settings.AUTH_PASSWORD_RESET_RATE_LIMIT_COUNT,
        window_seconds=settings.AUTH_PASSWORD_RESET_TTL_SECONDS,
        detail="Too many password reset requests.",
    )


def _audit(
    event_type: str,
    account: Account | None = None,
    email_attempted: str | None = None,
    request: Any = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    audit_log = LoginAuditLog.objects.create(
        account=account,
        email_attempted=email_attempted,
        event_type=event_type,
        ip_address=_request_ip(request),
        user_agent=_request_user_agent(request),
        metadata=metadata or {},
    )
    publish_auth_event(
        event_type=f"Auth{event_type.title().replace('_', '')}",
        aggregate_id=audit_log.id,
        payload={
            "account_id": str(account.id) if account else None,
            "email_attempted": email_attempted,
            "event_type": event_type,
        },
    )


def publish_auth_event(*, event_type: str, aggregate_id, payload: dict[str, Any]) -> dict[str, Any]:
    return publish_kafka_event(
        event_type=event_type,
        aggregate_id=aggregate_id,
        producer_service=settings.SERVICE_NAME,
        payload=payload,
    )


def encode_token(
    *,
    account: Account,
    credential: Credential,
    token_type: str,
    token_jti: uuid.UUID,
    expires_at: datetime,
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
    expires_at: datetime,
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
    _enforce_login_rate_limit(email=normalized_email, request=request)
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
    _validate_password_policy(temporary_password, field_name="temporary_password")
    normalized_scope_id = _validate_scope(scope_type, scope_id)
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
            scope_id=normalized_scope_id,
            assigned_by_account=actor_account,
            request=request,
        )
    _audit_authorization(
        AUTH_ACCOUNT_CREATED_AUDIT_EVENT,
        actor_account=actor_account,
        target_account=account,
        scope_type=scope_type,
        scope_id=normalized_scope_id,
        request=request,
        metadata={"role_code": role_code},
    )
    publish_auth_event(
        event_type="AuthAccountCreated",
        aggregate_id=account.id,
        payload={"account_id": str(account.id), "email": account.email, "status": account.status},
    )
    return account


@transaction.atomic
def request_password_reset(*, email: str, request: Any = None) -> str | None:
    normalized_email = email.strip().lower()
    _enforce_password_reset_rate_limit(email=normalized_email, request=request)

    try:
        account = Account.objects.select_related("credential").get(email__iexact=normalized_email)
    except Account.DoesNotExist:
        _audit(LoginAuditEvent.PASSWORD_RESET, email_attempted=normalized_email, request=request)
        return None

    if not account.is_active:
        _audit(
            LoginAuditEvent.PASSWORD_RESET,
            account=account,
            email_attempted=normalized_email,
            request=request,
        )
        return None

    raw_token = secrets.token_urlsafe(32)
    expires_at = timezone.now() + timedelta(seconds=settings.AUTH_PASSWORD_RESET_TTL_SECONDS)
    reset_token = PasswordResetToken.objects.create(
        account=account,
        token_hash=hash_token(raw_token),
        requested_ip=_request_ip(request),
        expires_at=expires_at,
    )
    try:
        _redis_client().setex(
            _password_reset_key(raw_token),
            settings.AUTH_PASSWORD_RESET_TTL_SECONDS,
            str(reset_token.id),
        )
    except (redis.RedisError, OSError) as exc:
        reset_token.status = PasswordResetStatus.REVOKED
        reset_token.save(update_fields=["status"])
        raise RedisSecurityUnavailable("Password reset is temporarily unavailable.") from exc

    _audit(LoginAuditEvent.PASSWORD_RESET, account=account, request=request)
    return raw_token


def confirm_password_reset(*, token: str, new_password: str) -> None:
    _validate_password_policy(new_password, field_name="new_password")
    token_hash = hash_token(token)
    reset_token = (
        PasswordResetToken.objects.select_related("account", "account__credential")
        .filter(token_hash=token_hash, status=PasswordResetStatus.PENDING)
        .order_by("-created_at")
        .first()
    )
    if reset_token is None:
        raise ValidationError({"token": "Password reset token is invalid."})

    if reset_token.expires_at <= timezone.now():
        PasswordResetToken.objects.filter(id=reset_token.id).update(
            status=PasswordResetStatus.EXPIRED,
        )
        raise ValidationError({"token": "Password reset token has expired."})

    client = _redis_client()
    try:
        redis_token_id = client.get(_password_reset_key(token))
    except (redis.RedisError, OSError) as exc:
        raise RedisSecurityUnavailable("Password reset is temporarily unavailable.") from exc

    if redis_token_id != str(reset_token.id):
        PasswordResetToken.objects.filter(id=reset_token.id).update(
            status=PasswordResetStatus.EXPIRED,
        )
        raise ValidationError({"token": "Password reset token has expired."})

    with transaction.atomic():
        reset_token = (
            PasswordResetToken.objects.select_for_update()
            .select_related("account", "account__credential")
            .get(id=reset_token.id, status=PasswordResetStatus.PENDING)
        )
        credential = reset_token.account.credential
        credential.password_hash = make_password(new_password)
        credential.must_change_password = False
        credential.password_changed_at = timezone.now()
        credential.save(
            update_fields=[
                "password_hash",
                "must_change_password",
                "password_changed_at",
                "updated_at",
            ]
        )

        reset_token.status = PasswordResetStatus.USED
        reset_token.used_at = timezone.now()
        reset_token.save(update_fields=["status", "used_at"])
        revoke_account_tokens(reset_token.account, reason=BlacklistReason.PASSWORD_CHANGE)
    try:
        client.delete(_password_reset_key(token))
    except (redis.RedisError, OSError):
        pass


def issue_otp(*, purpose: str, subject: str, code: str) -> None:
    key = _otp_key(purpose=purpose, subject=subject)
    payload = {"code_hash": hash_token(code), "attempts": 0}
    if not set_json_cache(_redis_client(), key, payload, settings.AUTH_OTP_TTL_SECONDS):
        raise RedisSecurityUnavailable("OTP storage is temporarily unavailable.")


def verify_otp(*, purpose: str, subject: str, code: str) -> bool:
    key = _otp_key(purpose=purpose, subject=subject)
    client = _redis_client()
    try:
        cached = cast(str | bytes | bytearray | None, client.get(key))
    except (redis.RedisError, OSError) as exc:
        raise RedisSecurityUnavailable("OTP verification is temporarily unavailable.") from exc
    if not cached:
        return False
    try:
        payload = json.loads(cached)
    except (TypeError, ValueError):
        return False

    attempts = int(payload.get("attempts", 0))
    if attempts >= settings.AUTH_OTP_MAX_ATTEMPTS:
        _delete_redis_key(client, key)
        return False

    if hmac.compare_digest(str(payload.get("code_hash", "")), hash_token(code)):
        _delete_redis_key(client, key)
        return True

    attempts += 1
    if attempts >= settings.AUTH_OTP_MAX_ATTEMPTS:
        _delete_redis_key(client, key)
        return False

    payload["attempts"] = attempts
    try:
        ttl = int(cast(int, client.ttl(key)))
        client.setex(key, ttl if ttl > 0 else settings.AUTH_OTP_TTL_SECONDS, json.dumps(payload))
    except (redis.RedisError, OSError) as exc:
        raise RedisSecurityUnavailable("OTP verification is temporarily unavailable.") from exc
    return False


def _delete_redis_key(client: redis.Redis, key: str) -> None:
    try:
        client.delete(key)
    except (redis.RedisError, OSError) as exc:
        raise RedisSecurityUnavailable("Redis key deletion is temporarily unavailable.") from exc


@transaction.atomic
def update_managed_account(
    account: Account,
    *,
    email=_UNSET,
    phone=_UNSET,
    status=_UNSET,
    actor_account: Account | None = None,
    request: Any = None,
    scope_type: str = "",
    scope_id: uuid.UUID | str | None = None,
) -> Account:
    update_fields = ["updated_at"]
    changed_fields = []
    revoke_tokens = False
    if email is not _UNSET:
        account.email = email.strip().lower()
        update_fields.append("email")
        changed_fields.append("email")
    if phone is not _UNSET:
        account.phone = phone or None
        update_fields.append("phone")
        changed_fields.append("phone")
    if status is not _UNSET:
        account.status = status
        update_fields.append("status")
        changed_fields.append("status")
        if status == AccountStatus.DEACTIVATED:
            account.deleted_at = timezone.now()
            update_fields.append("deleted_at")
            changed_fields.append("deleted_at")
            revoke_tokens = True
    account.save(update_fields=update_fields)
    if revoke_tokens:
        revoke_account_tokens(account, reason=BlacklistReason.ADMIN_REVOKE)
    normalized_scope_id = _validate_scope(scope_type, scope_id) if scope_type else None
    _audit_authorization(
        AUTH_ACCOUNT_UPDATED_AUDIT_EVENT,
        actor_account=actor_account,
        target_account=account,
        scope_type=scope_type,
        scope_id=normalized_scope_id,
        request=request,
        metadata={"changed_fields": changed_fields},
    )
    publish_auth_event(
        event_type="AuthAccountUpdated",
        aggregate_id=account.id,
        payload={"account_id": str(account.id), "email": account.email, "status": account.status},
    )
    return account


@transaction.atomic
def deactivate_managed_account(
    account: Account,
    *,
    actor_account: Account | None = None,
    request: Any = None,
    scope_type: str = "",
    scope_id: uuid.UUID | str | None = None,
) -> Account:
    account.status = AccountStatus.DEACTIVATED
    account.deleted_at = timezone.now()
    account.save(update_fields=["status", "deleted_at", "updated_at"])
    revoke_account_tokens(account, reason=BlacklistReason.ADMIN_REVOKE)
    normalized_scope_id = _validate_scope(scope_type, scope_id) if scope_type else None
    _audit_authorization(
        AUTH_ACCOUNT_DEACTIVATED_AUDIT_EVENT,
        actor_account=actor_account,
        target_account=account,
        scope_type=scope_type,
        scope_id=normalized_scope_id,
        request=request,
    )
    publish_auth_event(
        event_type="AuthAccountDeactivated",
        aggregate_id=account.id,
        payload={"account_id": str(account.id), "email": account.email, "status": account.status},
    )
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
    blacklist_token_jti(
        token_jti,
        refresh_expires_at,
        account=account,
        reason=BlacklistReason.LOGOUT,
    )

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
    return _key_builder().key(
        "permission-cache",
        "check",
        [str(account_id), permission_code, scope_type, normalized_scope],
    )


def _permission_cache_prefix(account_id: uuid.UUID | str | None = None) -> str:
    if account_id:
        return _key_builder().prefix_for("permission-cache", "check", str(account_id))
    return _key_builder().prefix_for("permission-cache", "check")


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
    audit_log = AuthorizationAuditLog.objects.create(
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
    publish_auth_event(
        event_type=f"Authorization{event_type.title().replace('_', '')}",
        aggregate_id=audit_log.id,
        payload={
            "actor_account_id": str(actor_account.id) if actor_account else None,
            "target_account_id": str(target_account.id) if target_account else None,
            "role_code": role.code if role else None,
            "permission_code": permission.code if permission else None,
            "scope_type": scope_type,
            "scope_id": str(scope_id) if scope_id else None,
            "event_type": event_type,
        },
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
        return _has_permission_from_database(
            account,
            permission_code,
            scope_type,
            normalized_scope_id,
        )

    allowed = _has_permission_from_database(
        account,
        permission_code,
        scope_type,
        normalized_scope_id,
    )
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
    role_permission, created = RolePermission.objects.get_or_create(
        role=role,
        permission=permission,
    )
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
