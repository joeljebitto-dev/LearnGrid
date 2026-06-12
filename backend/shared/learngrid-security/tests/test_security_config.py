import pytest

from learngrid_security import (
    ProductionSecurityError,
    apply_django_security_defaults,
    env_bool,
    env_int,
    env_list,
    require_production_env,
)


def test_env_helpers_normalize_common_values():
    environ = {
        "FEATURE": "yes",
        "COUNT": "5",
        "ORIGINS": "https://app.example.com, https://admin.example.com ,,",
    }

    assert env_bool("FEATURE", environ=environ)
    assert env_int("COUNT", default=1, minimum=1, environ=environ) == 5
    assert env_list("ORIGINS", environ=environ) == [
        "https://app.example.com",
        "https://admin.example.com",
    ]


def test_require_production_env_rejects_missing_and_insecure_values():
    with pytest.raises(ProductionSecurityError):
        require_production_env(["DJANGO_SECRET_KEY"], environ={})

    with pytest.raises(ProductionSecurityError):
        require_production_env(
            ["DJANGO_SECRET_KEY"],
            environ={"DJANGO_SECRET_KEY": "insecure-local-change-me"},
        )

    require_production_env(
        ["DJANGO_SECRET_KEY"],
        environ={"DJANGO_SECRET_KEY": "prod-secret-value-with-entropy"},
    )


def test_apply_django_security_defaults_sets_secure_runtime_options(monkeypatch):
    monkeypatch.setenv("DJANGO_SECURE_HSTS_SECONDS", "86400")
    namespace = {}

    apply_django_security_defaults(namespace, csrf_trusted_origins=["https://app.example.com"])

    assert namespace["DEBUG"] is False
    assert namespace["SECURE_SSL_REDIRECT"] is True
    assert namespace["SECURE_PROXY_SSL_HEADER"] == ("HTTP_X_FORWARDED_PROTO", "https")
    assert namespace["SECURE_HSTS_SECONDS"] == 86400
    assert namespace["SECURE_HSTS_INCLUDE_SUBDOMAINS"] is True
    assert namespace["SESSION_COOKIE_SECURE"] is True
    assert namespace["CSRF_COOKIE_SECURE"] is True
    assert namespace["X_FRAME_OPTIONS"] == "DENY"
    assert namespace["CSRF_TRUSTED_ORIGINS"] == ["https://app.example.com"]
