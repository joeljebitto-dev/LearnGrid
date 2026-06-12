# Backend Architecture

Source: [SRD.pdf](SRD.pdf)

## BE-001 Service Pattern
Each backend service is a Django REST Framework application with a clean internal structure:

```text
config/
apps/<domain>/models.py
apps/<domain>/serializers.py
apps/<domain>/views.py
apps/<domain>/services.py
apps/<domain>/selectors.py
apps/<domain>/permissions.py
apps/<domain>/urls.py
apps/<domain>/tests/
```

## BE-002 Layer Responsibilities
| Layer | Responsibility |
| --- | --- |
| `views.py` | HTTP request and response logic only |
| `serializers.py` | Validation and representation |
| `services.py` | Business workflows and write operations |
| `selectors.py` | Optimized read queries |
| `permissions.py` | Role and object-level authorization |
| `models.py` | Database schema and constraints |

## BE-003 API Standards
- Protected APIs must enforce backend authorization.
- List APIs must support pagination, filtering, and sorting.
- APIs must expose OpenAPI documentation at `/api/schema/` and `/api/docs/` through
  `drf-spectacular`.
- APIs must validate all inputs through serializers and schema checks.
- API responses must handle validation errors, permission failures, empty states, and retry-safe failures.
- Sensitive endpoints must use Redis-backed rate limiting.

## BE-004 Data Standards
- Follow [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) for table ownership and field-level schema.
- Use migrations for all schema changes.
- Use indexes for foreign keys, lookup fields, status fields, and frequent filters.
- Avoid N+1 queries with `select_related`, `prefetch_related`, optimized serializers, and selectors.
- Use transactions for multi-step writes inside a service boundary.

## BE-005 Event Standards
- Kafka events follow [SPEC-020](specs/020-kafka-eventing.md) and the implemented [EVT-020](event-design/EVT-020-kafka-eventing.md) design.
- Shared event code lives in [backend/shared/learngrid-events](../backend/shared/learngrid-events).
- Events include `event_id`, `event_type`, `aggregate_id`, `producer_service`, `timestamp`, `version`, `correlation_id`, and `payload`.
- Producers publish after database commit where possible and fall back to local logging when `KAFKA_ENABLED=false`.
- Consumers are idempotent and use retry and dead-letter topics.
- Management commands support `kafka_consume`, `kafka_retry_dlq`, and `kafka_consumer_lag`.

## BE-006 Redis Standards
- Redis helpers live in [backend/shared/learngrid-redis](../backend/shared/learngrid-redis).
- Redis keys follow `lg:{REDIS_ENV}:{service}:{workload}:{name}:{suffix}`.
- Raw emails, IP addresses, query payloads, OTP subjects, and reset tokens must be hashed before
  being included in key suffixes.
- Cache workloads fall back to source-of-truth reads when Redis is unavailable.
- Security workloads such as rate limits, OTPs, password reset, and distributed locks fail closed
  when Redis is unavailable.
- Production Redis uses the on-prem Kubernetes runtime baseline from [T-023](tasks/T-023-ci-cd-deployment-observability.md);
  future Sentinel/Cluster hardening can evolve from that deployment topology.

## BE-007 Security Standards
- Security helpers live in [backend/shared/learngrid-security](../backend/shared/learngrid-security).
- Production settings must require secrets and reject local-only placeholder values.
- Production settings must enable SSL redirect, proxy SSL detection, HSTS, secure cookies, content
  sniffing protection, frame denial, and strict referrer policy.
- API inputs must be validated through serializers and service-level checks before writes.
- Sensitive writes must produce durable audit records.
- File uploads must validate MIME type, extension, file size, object key safety, and optional
  malware scanning when configured.
- Kubernetes security baseline templates live under
  [infrastructure/kubernetes/security-baseline](../infrastructure/kubernetes/security-baseline);
  full deployment manifests live under [infrastructure/helm](../infrastructure/helm).

## BE-008 Runtime And Observability Standards
- Backend services expose `/health/`, `/health/live/`, `/health/ready/`, and `/metrics/`.
- Readiness checks PostgreSQL connectivity; Redis and Kafka outages are handled by workload-specific
  fallback or fail-closed behavior rather than global readiness.
- Backend services run under Gunicorn in production containers and emit JSON logs to stdout.
- Sentry and OTLP tracing are enabled only when `SENTRY_DSN` and `OTEL_EXPORTER_OTLP_ENDPOINT` are
  configured.

## BE-009 Testing And Quality Standards
- Each backend service includes schema smoke tests for `/api/schema/` and `/api/docs/`.
- Service CI runs `ruff check`, `ruff format --check`, `mypy`, Django checks, migration dry-runs,
  and pytest.
- Repo-level tests cover OpenAPI/Kafka contracts, Compose-backed PostgreSQL/Redis/Kafka/MinIO
  integration, Selenium journey smoke tests, and k6 load smoke scripts.

## BE-010 Related Tasks
See [TASKS.md](TASKS.md) for implementation checklists, especially [T-001](tasks/T-001-project-setup.md), [T-020](tasks/T-020-kafka-eventing.md), [T-021](tasks/T-021-redis-architecture.md), [T-022](tasks/T-022-security.md), [T-023](tasks/T-023-ci-cd-deployment-observability.md), and [T-024](tasks/T-024-testing-quality.md).
