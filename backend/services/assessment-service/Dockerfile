# syntax=docker/dockerfile:1.7
ARG SERVICE_NAME=assessment-service
FROM python:3.12-slim AS runtime
ARG SERVICE_NAME

ENV DJANGO_SETTINGS_MODULE=config.settings.production \
    PATH="/home/learngrid/.local/bin:${PATH}" \
    PORT=8000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system learngrid \
    && useradd --system --gid learngrid --home-dir /home/learngrid --create-home learngrid \
    && apt-get update \
    && apt-get install --no-install-recommends --yes curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/shared ./backend/shared
COPY backend/services/${SERVICE_NAME}/pyproject.toml backend/services/${SERVICE_NAME}/poetry.lock ./backend/services/${SERVICE_NAME}/
WORKDIR /app/backend/services/${SERVICE_NAME}
RUN pip install --no-cache-dir poetry==2.2.1 \
    && poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

COPY backend/services/${SERVICE_NAME} /app/backend/services/${SERVICE_NAME}
RUN DJANGO_SETTINGS_MODULE=config.settings.local python manage.py collectstatic --noinput

USER learngrid
EXPOSE 8000
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${GUNICORN_WORKERS:-2} --timeout ${GUNICORN_TIMEOUT_SECONDS:-60} --access-logfile - --error-logfile -"]
