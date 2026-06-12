# T-020 Kafka Eventing Implementation Plan

## Summary
Implement Kafka eventing as a shared backend capability, replacing local-only event logging with a Kafka-capable producer/consumer baseline. Use Apache Kafka in local Docker Compose, keep existing synchronous REST calls unchanged, and add retry, dead-letter, idempotency, and lag visibility.

## Key Changes
- Add a shared Python package: `backend/shared/learngrid-events`.
  - Event envelope fields: `event_id`, `event_type`, `aggregate_id`, `producer_service`, `timestamp`, `version`, `correlation_id`, and `payload`.
  - Topic catalog: `user.events`, `course.events`, `enrollment.events`, `content.events`, `progress.events`, `assessment.events`, `grading.events`, `notification.events`, `audit.events`, and `analytics.events`.
  - Derived topics for every base topic: `<topic>.retry` and `<topic>.dlq`.
  - Producer helper publishes after DB commit where possible using `transaction.on_commit`.
  - Consumer helper validates envelope shape, enforces idempotency through service handlers, retries failed messages, and sends poison messages to DLQ after max attempts.
  - Monitoring helper reports consumer group lag as JSON.

- Add Kafka infrastructure.
  - Add `kafka`, `kafka-ui`, and `kafka-init` services to `docker-compose.yml`.
  - Local Kafka broker: `127.0.0.1:9092`.
  - Kafka UI: `http://127.0.0.1:8090`.
  - `kafka-init` creates all base, retry, and DLQ topics.
  - Update `pnpm dev`, `pnpm dev:fast`, and `pnpm dev:infra` so Kafka starts with the local stack.

- Wire backend services to the shared package.
  - Add the shared path dependency to relevant service `pyproject.toml` files.
  - Add Kafka settings to each service: `KAFKA_ENABLED`, `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_CLIENT_ID`, `KAFKA_DEFAULT_PARTITIONS`, `KAFKA_REPLICATION_FACTOR`, `KAFKA_CONSUMER_GROUP`, `KAFKA_MAX_RETRY_ATTEMPTS`.
  - Producers:
    - `auth-service` publishes audit/security events to `audit.events`.
    - `user-service` publishes profile/account lifecycle events to `user.events`.
    - `course-service` publishes course and lesson events to `course.events`.
    - `content-service` publishes upload/publish/delete events to `content.events`.
    - `enrollment-service` publishes enrollment/access events to `enrollment.events`.
    - `progress-service` publishes progress/completion events to `progress.events`.
    - `assessment-service` publishes assessment, quiz, and assignment events to `assessment.events`.
    - `grading-service` publishes grade and certificate events to `grading.events`.
    - `notification-service` publishes notification processing events to `notification.events`.
    - `analytics-service` publishes report/event-ingestion events to `analytics.events`.
  - Consumers:
    - `analytics-service` consumes all base topics into `event_facts`.
    - `notification-service` consumes enrollment/progress/grading events for in-app notification workflows.
    - `progress-service` consumes assessment progress events such as `QuizSubmitted` and `AssignmentSubmitted`.
  - Existing REST APIs remain the source for synchronous request-response workflows.

- Add management commands through the shared Django app.
  - `python manage.py kafka_consume --topic <topic> --group <group> --handler <handler-name>`
  - `python manage.py kafka_retry_dlq --topic <topic>.dlq --event-id <uuid>`
  - `python manage.py kafka_consumer_lag --group <group>`
  - Service-specific handler maps live in settings so consumers are explicit and testable.

## Documentation
- Add `docs/event-design/EVT-020-kafka-eventing.md` and `docs/event-design/README.md`.
- Update `DEVELOPMENT.md`, `BACKEND_ARCHITECTURE.md`, `DATABASE_SCHEMA.md`, `DB_STRUCTURE.md`, `TESTING_STRATEGY.md`, `CHANGELOG.md`, `LIVING_DOCUMENT.md`, `.env.example`, and `docs/tasks/T-020-kafka-eventing.md`.
- Replace stale “Kafka transport remains future T-020” notes in implemented design docs with links to the new eventing design.
- Mark `T-020.01` through `T-020.08` complete only after verification passes.

## Test Plan
- Shared package tests:
  - Envelope creation and validation.
  - Topic catalog includes base, retry, and DLQ topics.
  - Producer serializes valid messages and rejects invalid messages.
  - Consumer handles success, duplicate, retry, and DLQ paths with a fake Kafka adapter.
  - Consumer lag helper returns stable JSON.
- Service tests:
  - Existing event-emitting workflows still return the expected envelope.
  - Producers use the correct topic per service.
  - Analytics consumer stores event facts idempotently.
  - Notification consumer processes supported events idempotently.
  - Progress consumer ignores duplicate progress events.
- Infrastructure checks:
  - `docker compose config`
  - Kafka topic init script dry-run/static validation.
  - `bash -n scripts/run-dev.sh`
- Verification:
  - Shared package: `poetry run ruff check .`, `poetry run pytest`
  - Changed backend services: `poetry lock`, `poetry run ruff check .`, `poetry run python manage.py check`, `poetry run pytest`
  - Root gateway/dev checks remain passing.

## Assumptions
- Use Apache Kafka-compatible local infrastructure, not Redpanda.
- Use Kafka for asynchronous workflows only; do not replace synchronous service API calls.
- Local/test mode can use a fake Kafka adapter, but `pnpm dev` starts a real local Kafka broker.
- T-020 adds Kafka UI and lag commands for baseline lag visibility; full Prometheus/Grafana observability remains T-023.
