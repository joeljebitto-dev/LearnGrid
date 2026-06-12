import os
from pathlib import Path

import dj_database_url
from learngrid_observability.django import configure_django_observability

BASE_DIR = Path(__file__).resolve().parents[2]

SERVICE_ID = "SVC-005"
SERVICE_NAME = "enrollment-service"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure-local-enrollment-service")
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
    "apps.enrollments",
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
KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "false").lower() == "true"
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092")
KAFKA_CLIENT_ID = os.getenv("KAFKA_CLIENT_ID", SERVICE_NAME)
KAFKA_DEFAULT_PARTITIONS = int(os.getenv("KAFKA_DEFAULT_PARTITIONS", "3"))
KAFKA_REPLICATION_FACTOR = int(os.getenv("KAFKA_REPLICATION_FACTOR", "1"))
KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", f"{SERVICE_NAME}-consumer")
KAFKA_MAX_RETRY_ATTEMPTS = int(os.getenv("KAFKA_MAX_RETRY_ATTEMPTS", "3"))
KAFKA_EVENT_HANDLERS: dict[str, str] = {}
AUTH_SERVICE_BASE_URL = os.getenv("AUTH_SERVICE_BASE_URL", "http://127.0.0.1:8001")
AUTH_JWT_SIGNING_KEY = os.getenv(
    "AUTH_JWT_SIGNING_KEY",
    "insecure-local-auth-service-change-me-32bytes",
)
AUTH_JWT_ISSUER = os.getenv("AUTH_JWT_ISSUER", "learngrid-auth-service")
AUTH_JWT_ALGORITHM = os.getenv("AUTH_JWT_ALGORITHM", "HS256")
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
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.enrollments.authentication.JWTAuthentication"],
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
