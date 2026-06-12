import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parents[2]

SERVICE_ID = "SVC-004"
SERVICE_NAME = "content-service"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure-local-content-service")
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
    "learngrid_events",
    "apps.content",
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
KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "false").lower() == "true"
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092")
KAFKA_CLIENT_ID = os.getenv("KAFKA_CLIENT_ID", SERVICE_NAME)
KAFKA_DEFAULT_PARTITIONS = int(os.getenv("KAFKA_DEFAULT_PARTITIONS", "3"))
KAFKA_REPLICATION_FACTOR = int(os.getenv("KAFKA_REPLICATION_FACTOR", "1"))
KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", f"{SERVICE_NAME}-consumer")
KAFKA_MAX_RETRY_ATTEMPTS = int(os.getenv("KAFKA_MAX_RETRY_ATTEMPTS", "3"))
KAFKA_EVENT_HANDLERS = {}
CONTENT_STORAGE_PROVIDER = os.getenv("CONTENT_STORAGE_PROVIDER", "minio")
CONTENT_STORAGE_BUCKET = os.getenv("CONTENT_STORAGE_BUCKET", "learngrid-content")
CONTENT_MINIO_ENDPOINT_URL = os.getenv("CONTENT_MINIO_ENDPOINT_URL", "http://127.0.0.1:9000")
CONTENT_MINIO_ACCESS_KEY = os.getenv("CONTENT_MINIO_ACCESS_KEY", "learngrid")
CONTENT_MINIO_SECRET_KEY = os.getenv("CONTENT_MINIO_SECRET_KEY", "learngrid-minio-secret")
CONTENT_MINIO_SECURE = os.getenv("CONTENT_MINIO_SECURE", "false").lower() == "true"
CONTENT_MAX_UPLOAD_SIZE_BYTES = int(os.getenv("CONTENT_MAX_UPLOAD_SIZE_BYTES", "104857600"))
CONTENT_ALLOWED_MIME_TYPES = [
    mime.strip()
    for mime in os.getenv(
        "CONTENT_ALLOWED_MIME_TYPES",
        "video/mp4,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,image/png,image/jpeg,text/plain",
    ).split(",")
    if mime.strip()
]
CONTENT_SIGNED_ACCESS_TTL_SECONDS = int(os.getenv("CONTENT_SIGNED_ACCESS_TTL_SECONDS", "300"))
CONTENT_PRESIGNED_UPLOAD_TTL_SECONDS = int(os.getenv("CONTENT_PRESIGNED_UPLOAD_TTL_SECONDS", "900"))
CONTENT_PRESIGNED_DOWNLOAD_TTL_SECONDS = int(os.getenv("CONTENT_PRESIGNED_DOWNLOAD_TTL_SECONDS", "300"))
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
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.content.authentication.JWTAuthentication"],
}
