from __future__ import annotations

import json
import logging
import os
from collections.abc import MutableMapping
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        for field in ("service", "request_id", "correlation_id"):
            value = getattr(record, field, None)
            if value:
                payload[field] = value
        return json.dumps(payload, default=str, separators=(",", ":"))


def configure_django_observability(settings_namespace: MutableMapping[str, Any]) -> None:
    service_name = str(settings_namespace.get("SERVICE_NAME", "learngrid-service"))
    _configure_runtime_settings(settings_namespace, service_name)
    _configure_sentry(service_name)
    _configure_opentelemetry(service_name)


def _configure_runtime_settings(
    settings_namespace: MutableMapping[str, Any],
    service_name: str,
) -> None:
    settings_namespace.setdefault("PORT", int(os.getenv("PORT", "8000")))
    settings_namespace.setdefault("GUNICORN_WORKERS", int(os.getenv("GUNICORN_WORKERS", "2")))
    settings_namespace.setdefault(
        "GUNICORN_TIMEOUT_SECONDS",
        int(os.getenv("GUNICORN_TIMEOUT_SECONDS", "60")),
    )
    settings_namespace.setdefault("SENTRY_DSN", os.getenv("SENTRY_DSN", ""))
    settings_namespace.setdefault(
        "SENTRY_ENVIRONMENT",
        os.getenv("SENTRY_ENVIRONMENT", os.getenv("DJANGO_ENV", "local")),
    )
    settings_namespace.setdefault(
        "SENTRY_TRACES_SAMPLE_RATE",
        float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0")),
    )
    settings_namespace.setdefault(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", ""),
    )
    settings_namespace.setdefault(
        "OTEL_SERVICE_NAME",
        os.getenv("OTEL_SERVICE_NAME", service_name),
    )
    settings_namespace.setdefault(
        "LOGGING",
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"json": {"()": "learngrid_observability.django.JsonFormatter"}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                },
            },
            "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
            "loggers": {
                "django.server": {"handlers": ["console"], "level": "INFO", "propagate": False},
                "django.request": {"handlers": ["console"], "level": "INFO", "propagate": False},
            },
        },
    )


def _configure_sentry(service_name: str) -> None:
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
    except Exception:
        logging.getLogger(__name__).warning("Sentry SDK is unavailable; skipping setup")
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("SENTRY_ENVIRONMENT", os.getenv("DJANGO_ENV", "local")),
        integrations=[DjangoIntegration()],
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0")),
        release=os.getenv("RELEASE_SHA", ""),
        server_name=service_name,
        send_default_pii=False,
    )


def _configure_opentelemetry(service_name: str) -> None:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except Exception:
        logging.getLogger(__name__).warning(
            "OpenTelemetry packages are unavailable; skipping setup"
        )
        return

    if not isinstance(trace.get_tracer_provider(), TracerProvider):
        provider = TracerProvider(
            resource=Resource.create(
                {
                    "service.name": os.getenv("OTEL_SERVICE_NAME", service_name),
                    "deployment.environment": os.getenv("SENTRY_ENVIRONMENT", "local"),
                },
            ),
        )
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        trace.set_tracer_provider(provider)
    DjangoInstrumentor().instrument()
