from __future__ import annotations

import json
import logging

from learngrid_observability.django import JsonFormatter, configure_django_observability


def test_configure_django_observability_defaults(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    namespace = {"SERVICE_NAME": "auth-service"}

    configure_django_observability(namespace)

    assert namespace["PORT"] == 8000
    assert namespace["GUNICORN_WORKERS"] == 2
    assert namespace["OTEL_SERVICE_NAME"] == "auth-service"
    assert namespace["LOGGING"]["formatters"]["json"]["()"].endswith("JsonFormatter")


def test_json_formatter_outputs_structured_log():
    record = logging.LogRecord("learngrid", logging.INFO, __file__, 1, "hello %s", ("world",), None)
    record.service = "auth-service"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "learngrid"
    assert payload["message"] == "hello world"
    assert payload["service"] == "auth-service"
