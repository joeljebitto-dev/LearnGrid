import os
from pathlib import Path

import dj_database_url
from learngrid_observability.django import configure_django_observability

BASE_DIR = Path(__file__).resolve().parents[2]

SERVICE_ID = "SVC-001"
SERVICE_NAME = "auth-service"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure-local-auth-service-change-me-32bytes")
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django_prometheus",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "learngrid_events",
    "apps.authentication",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {},
    },
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=60,
    )
}

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_ENV = os.getenv("REDIS_ENV", "local")
REDIS_SENTINEL_URLS = os.getenv("REDIS_SENTINEL_URLS", "")
REDIS_SENTINEL_MASTER_NAME = os.getenv("REDIS_SENTINEL_MASTER_NAME", "mymaster")
REDIS_SENTINEL_PASSWORD = os.getenv("REDIS_SENTINEL_PASSWORD")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS = float(
    os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS", "0.2"),
)
REDIS_SOCKET_TIMEOUT_SECONDS = float(os.getenv("REDIS_SOCKET_TIMEOUT_SECONDS", "0.2"))
REDIS_LOCK_TTL_SECONDS = int(os.getenv("REDIS_LOCK_TTL_SECONDS", "30"))
KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "false").lower() == "true"
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092")
KAFKA_CLIENT_ID = os.getenv("KAFKA_CLIENT_ID", SERVICE_NAME)
KAFKA_DEFAULT_PARTITIONS = int(os.getenv("KAFKA_DEFAULT_PARTITIONS", "3"))
KAFKA_REPLICATION_FACTOR = int(os.getenv("KAFKA_REPLICATION_FACTOR", "1"))
KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", f"{SERVICE_NAME}-consumer")
KAFKA_MAX_RETRY_ATTEMPTS = int(os.getenv("KAFKA_MAX_RETRY_ATTEMPTS", "3"))
KAFKA_EVENT_HANDLERS: dict[str, str] = {}
AUTH_ACCESS_TOKEN_LIFETIME_SECONDS = int(os.getenv("AUTH_ACCESS_TOKEN_LIFETIME_SECONDS", "300"))
AUTH_REFRESH_TOKEN_LIFETIME_SECONDS = int(
    os.getenv("AUTH_REFRESH_TOKEN_LIFETIME_SECONDS", "604800")
)
AUTH_JWT_ISSUER = os.getenv("AUTH_JWT_ISSUER", "learngrid-auth-service")
AUTH_JWT_ALGORITHM = "HS256"
AUTH_JWT_SIGNING_KEY = os.getenv("AUTH_JWT_SIGNING_KEY", SECRET_KEY)
AUTH_TOKEN_HASH_KEY = os.getenv("AUTH_TOKEN_HASH_KEY", SECRET_KEY)
AUTH_PASSWORD_MIN_LENGTH = int(os.getenv("AUTH_PASSWORD_MIN_LENGTH", "12"))
AUTH_PERMISSION_CACHE_TTL_SECONDS = int(os.getenv("AUTH_PERMISSION_CACHE_TTL_SECONDS", "300"))
AUTH_LOGIN_RATE_LIMIT_COUNT = int(os.getenv("AUTH_LOGIN_RATE_LIMIT_COUNT", "5"))
AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS = int(
    os.getenv("AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS", "900"),
)
AUTH_PASSWORD_RESET_RATE_LIMIT_COUNT = int(os.getenv("AUTH_PASSWORD_RESET_RATE_LIMIT_COUNT", "3"))
AUTH_PASSWORD_RESET_TTL_SECONDS = int(os.getenv("AUTH_PASSWORD_RESET_TTL_SECONDS", "900"))
AUTH_PASSWORD_RESET_DEBUG_RETURN_TOKEN = (
    os.getenv("AUTH_PASSWORD_RESET_DEBUG_RETURN_TOKEN", "false").lower() == "true"
)
AUTH_OTP_TTL_SECONDS = int(os.getenv("AUTH_OTP_TTL_SECONDS", "300"))
AUTH_OTP_MAX_ATTEMPTS = int(os.getenv("AUTH_OTP_MAX_ATTEMPTS", "5"))
AUTH_OIDC_ENABLED = os.getenv("AUTH_OIDC_ENABLED", "false").lower() == "true"
AUTH_OIDC_PROVIDER_LABEL = os.getenv("AUTH_OIDC_PROVIDER_LABEL", "Organization SSO")
AUTH_OIDC_ISSUER_URL = os.getenv("AUTH_OIDC_ISSUER_URL", "").rstrip("/")
AUTH_OIDC_CLIENT_ID = os.getenv("AUTH_OIDC_CLIENT_ID", "")
AUTH_OIDC_CLIENT_SECRET = os.getenv("AUTH_OIDC_CLIENT_SECRET", "")
AUTH_OIDC_REDIRECT_URI = os.getenv("AUTH_OIDC_REDIRECT_URI", "")
AUTH_OIDC_SCOPES = " ".join(
    scope.strip()
    for scope in os.getenv("AUTH_OIDC_SCOPES", "openid email profile").replace(",", " ").split()
    if scope.strip()
)
AUTH_OIDC_STATE_TTL_SECONDS = int(os.getenv("AUTH_OIDC_STATE_TTL_SECONDS", "300"))
AUTH_OIDC_JWKS_CACHE_TTL_SECONDS = int(os.getenv("AUTH_OIDC_JWKS_CACHE_TTL_SECONDS", "3600"))
AUTH_OIDC_REQUIRE_EMAIL_VERIFIED = (
    os.getenv("AUTH_OIDC_REQUIRE_EMAIL_VERIFIED", "true").lower() == "true"
)
AUTH_OIDC_ALLOWED_ALGORITHMS = [
    item.strip()
    for item in os.getenv("AUTH_OIDC_ALLOWED_ALGORITHMS", "RS256").split(",")
    if item.strip()
]
AUTH_OIDC_CLIENT_AUTH_METHOD = os.getenv("AUTH_OIDC_CLIENT_AUTH_METHOD", "client_secret_post")
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": AUTH_PASSWORD_MIN_LENGTH},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.authentication.authentication.JWTAuthentication"],
}

SPECTACULAR_SETTINGS = {
    "TITLE": f"LearnGrid {SERVICE_NAME} API",
    "DESCRIPTION": f"OpenAPI schema for {SERVICE_NAME}.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    },
    "SECURITY": [{"bearerAuth": []}],
}
configure_django_observability(globals())
