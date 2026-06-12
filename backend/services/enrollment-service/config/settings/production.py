import os

from learngrid_security import apply_django_security_defaults, env_list, require_production_env

from .base import *  # noqa: F403

REQUIRED_PRODUCTION_ENV = [
    "DJANGO_SECRET_KEY",
    "DATABASE_URL",
    "DJANGO_ALLOWED_HOSTS",
    "CORS_ALLOWED_ORIGINS",
    "AUTH_JWT_SIGNING_KEY",
]

require_production_env(REQUIRED_PRODUCTION_ENV)

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")

apply_django_security_defaults(
    globals(),
    csrf_trusted_origins=env_list("CSRF_TRUSTED_ORIGINS", default=CORS_ALLOWED_ORIGINS),
)
