# OBS-023 Grafana Stack

Related task: [T-023](../tasks/T-023-ci-cd-deployment-observability.md)

## Signals
- Metrics: backend services expose `/metrics/` through `django-prometheus`; Prometheus scrapes
  annotated pods and exporters.
- Logs: backend services write JSON logs to stdout; Alloy forwards Kubernetes logs to Loki.
- Traces: backend services can export OTLP HTTP traces to Tempo when
  `OTEL_EXPORTER_OTLP_ENDPOINT` is set.
- Errors: backend and frontend Sentry initialization is enabled only when DSNs are configured.

## Dashboards
Grafana is provisioned with Prometheus, Loki, and Tempo datasources plus LearnGrid dashboards for
API latency/errors, Kafka lag, PostgreSQL, Redis, pod restarts, user activity, and assessment
submissions. Product activity panels are wired to stable metric names so application counters can
be added without changing dashboard layout.
