from pathlib import Path


SERVICES = [
    ("SVC-001", "auth-service", "authentication", "auth_db", 8001),
    ("SVC-002", "user-service", "users", "user_db", 8002),
    ("SVC-003", "course-service", "courses", "course_db", 8003),
    ("SVC-004", "content-service", "content", "content_db", 8004),
    ("SVC-005", "enrollment-service", "enrollments", "enrollment_db", 8005),
    ("SVC-006", "progress-service", "progress", "progress_db", 8006),
    ("SVC-007", "assessment-service", "assessments", "assessment_db", 8007),
    ("SVC-008", "grading-service", "grading", "grading_db", 8008),
    ("SVC-009", "notification-service", "notifications", "notification_db", 8009),
    ("SVC-010", "analytics-service", "analytics", "analytics_db", 8010),
]


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend" / "services"


def class_name(domain: str) -> str:
    return "".join(part.capitalize() for part in domain.split("_")) + "Config"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def pyproject(service: str) -> str:
    project_name = f"learngrid-{service}"
    return f"""[tool.poetry]
name = "{project_name}"
version = "0.1.0"
description = "LearnGrid LMS {service} baseline"
authors = ["LearnGrid LMS"]
package-mode = false

[tool.poetry.dependencies]
python = ">=3.12,<3.15"
django = "^5.2.8"
djangorestframework = "^3.16.1"
django-cors-headers = "^4.9.0"
dj-database-url = "^3.0.1"
psycopg = {{ version = "^3.2.12", extras = ["binary"] }}
redis = "^7.0.1"

[tool.poetry.group.dev.dependencies]
django-stubs = "^5.2.7"
djangorestframework-stubs = "^3.16.5"
mypy = "^1.18.2"
pytest = "^9.0.1"
pytest-django = "^4.11.1"
ruff = "^0.14.6"

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.test"
python_files = ["tests.py", "test_*.py", "*_tests.py"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.mypy]
python_version = "3.12"
plugins = ["mypy_django_plugin.main", "mypy_drf_plugin.main"]
ignore_missing_imports = true

[tool.django-stubs]
django_settings_module = "config.settings.test"

[build-system]
requires = ["poetry-core>=2.0.0,<3.0.0"]
build-backend = "poetry.core.masonry.api"
"""


def manage_py() -> str:
    return """#!/usr/bin/env python
import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
"""


def settings_base(service_id: str, service: str, domain: str) -> str:
    return f"""import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parents[2]

SERVICE_ID = "{service_id}"
SERVICE_NAME = "{service}"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure-local-{service}")
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
    "apps.{domain}",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = []
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {{
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", f"sqlite:///{{BASE_DIR / 'db.sqlite3'}}"),
        conn_max_age=60,
    )
}}

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
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

REST_FRAMEWORK = {{
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}}
"""


LOCAL_SETTINGS = """from .base import *  # noqa: F403

DEBUG = True
"""


TEST_SETTINGS = """from .base import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
"""


PRODUCTION_SETTINGS = """from .base import *  # noqa: F403

DEBUG = False
"""


def urls_py() -> str:
    return """from django.conf import settings
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health(_request):
    return Response({"service": settings.SERVICE_NAME, "status": "ok"})


urlpatterns = [
    path("health/", health, name="health"),
]
"""


def wsgi_py() -> str:
    return """import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_wsgi_application()
"""


def asgi_py() -> str:
    return """import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_asgi_application()
"""


def app_config(domain: str) -> str:
    return f"""from django.apps import AppConfig


class {class_name(domain)}(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.{domain}"
"""


def test_health(service: str) -> str:
    return f"""def test_health_endpoint(client):
    response = client.get("/health/")

    assert response.status_code == 200
    assert response.json() == {{"service": "{service}", "status": "ok"}}
"""


def env_example(db: str, port: int) -> str:
    return f"""DJANGO_SETTINGS_MODULE=config.settings.local
DJANGO_SECRET_KEY=insecure-local-change-me
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
SERVICE_PORT={port}
DATABASE_URL=postgresql://learngrid:learngrid@localhost:5432/{db}
REDIS_URL=redis://localhost:6379/0
"""


def main() -> None:
    for service_id, service, domain, db, port in SERVICES:
        root = BACKEND_ROOT / service
        write(root / "pyproject.toml", pyproject(service))
        write(root / "manage.py", manage_py())
        write(root / ".env.example", env_example(db, port))
        write(root / "config" / "__init__.py", "")
        write(root / "config" / "asgi.py", asgi_py())
        write(root / "config" / "wsgi.py", wsgi_py())
        write(root / "config" / "urls.py", urls_py())
        write(root / "config" / "settings" / "__init__.py", "")
        write(root / "config" / "settings" / "base.py", settings_base(service_id, service, domain))
        write(root / "config" / "settings" / "local.py", LOCAL_SETTINGS)
        write(root / "config" / "settings" / "test.py", TEST_SETTINGS)
        write(root / "config" / "settings" / "production.py", PRODUCTION_SETTINGS)
        write(root / "apps" / "__init__.py", "")
        write(root / "apps" / domain / "__init__.py", "")
        write(root / "apps" / domain / "apps.py", app_config(domain))
        write(root / "apps" / domain / "models.py", "")
        write(root / "apps" / domain / "serializers.py", "")
        write(root / "apps" / domain / "views.py", "")
        write(root / "apps" / domain / "services.py", "")
        write(root / "apps" / domain / "selectors.py", "")
        write(root / "apps" / domain / "permissions.py", "")
        write(root / "apps" / domain / "urls.py", "urlpatterns = []\n")
        write(root / "apps" / domain / "tests" / "__init__.py", "")
        write(root / "apps" / domain / "tests" / "test_health.py", test_health(service))


if __name__ == "__main__":
    main()
