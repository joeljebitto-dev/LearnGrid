from __future__ import annotations

import os
from collections.abc import Iterable, MutableMapping


class ProductionSecurityError(RuntimeError):
    """Raised when a production setting is missing or obviously unsafe."""


INSECURE_MARKERS = (
    "insecure-local",
    "change-me",
    "changeme",
    "learngrid-minio-secret",
)


def env_bool(
    name: str,
    *,
    default: bool = False,
    environ: MutableMapping[str, str] | None = None,
) -> bool:
    source = os.environ if environ is None else environ
    raw = source.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_int(
    name: str,
    *,
    default: int,
    minimum: int | None = None,
    environ: MutableMapping[str, str] | None = None,
) -> int:
    source = os.environ if environ is None else environ
    raw = source.get(name)
    value = default if raw is None or raw.strip() == "" else int(raw)
    if minimum is not None and value < minimum:
        raise ProductionSecurityError(f"{name} must be at least {minimum}.")
    return value


def env_list(
    name: str,
    *,
    default: Iterable[str] = (),
    environ: MutableMapping[str, str] | None = None,
) -> list[str]:
    source = os.environ if environ is None else environ
    raw = source.get(name)
    if raw is None:
        return [item for item in default if item]
    return [item.strip() for item in raw.split(",") if item.strip()]


def require_production_env(
    names: Iterable[str],
    *,
    environ: MutableMapping[str, str] | None = None,
    reject_insecure: bool = True,
) -> None:
    source = os.environ if environ is None else environ
    missing = [name for name in names if not source.get(name, "").strip()]
    if missing:
        raise ProductionSecurityError(
            "Missing required production environment variables: " + ", ".join(sorted(missing))
        )

    if reject_insecure:
        insecure = [name for name in names if _looks_insecure(source.get(name, ""))]
        if insecure:
            raise ProductionSecurityError(
                "Production environment variables contain local-only placeholder values: "
                + ", ".join(sorted(insecure))
            )


def apply_django_security_defaults(
    settings_namespace: MutableMapping[str, object],
    *,
    hsts_seconds: int | None = None,
    csrf_trusted_origins: Iterable[str] = (),
) -> None:
    resolved_hsts = env_int(
        "DJANGO_SECURE_HSTS_SECONDS",
        default=31536000 if hsts_seconds is None else hsts_seconds,
        minimum=0,
    )
    settings_namespace.update(
        {
            "DEBUG": False,
            "SECURE_SSL_REDIRECT": True,
            "SECURE_PROXY_SSL_HEADER": ("HTTP_X_FORWARDED_PROTO", "https"),
            "SECURE_HSTS_SECONDS": resolved_hsts,
            "SECURE_HSTS_INCLUDE_SUBDOMAINS": True,
            "SECURE_HSTS_PRELOAD": True,
            "SECURE_CONTENT_TYPE_NOSNIFF": True,
            "SECURE_REFERRER_POLICY": "strict-origin-when-cross-origin",
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
            "X_FRAME_OPTIONS": "DENY",
            "CSRF_TRUSTED_ORIGINS": list(csrf_trusted_origins),
        }
    )


def _looks_insecure(value: str) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return False
    return any(marker in normalized for marker in INSECURE_MARKERS)
