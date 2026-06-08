import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parents[2]

SERVICE_ID = "SVC-007"
SERVICE_NAME = "assessment-service"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure-local-assessment-service")
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "apps.assessments",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = []
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=60,
    )
}

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
AUTH_SERVICE_BASE_URL = os.getenv("AUTH_SERVICE_BASE_URL", "http://127.0.0.1:8001")
USER_SERVICE_BASE_URL = os.getenv("USER_SERVICE_BASE_URL", "http://127.0.0.1:8002")
COURSE_SERVICE_BASE_URL = os.getenv("COURSE_SERVICE_BASE_URL", "http://127.0.0.1:8003")
ENROLLMENT_SERVICE_BASE_URL = os.getenv("ENROLLMENT_SERVICE_BASE_URL", "http://127.0.0.1:8005")
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
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.assessments.authentication.JWTAuthentication"],
}
