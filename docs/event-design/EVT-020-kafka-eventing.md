# EVT-020 Kafka Eventing

Related task: [T-020](../tasks/T-020-kafka-eventing.md)  
Related spec: [SPEC-020](../specs/020-kafka-eventing.md)  
Related architecture: [BACKEND_ARCHITECTURE.md](../BACKEND_ARCHITECTURE.md)

## EVT-020-001 Purpose
LearnGrid uses Apache Kafka for asynchronous service events. Kafka is used for publish/consume workflows, analytics ingestion, notification triggers, progress updates, retries, dead-letter routing, and lag visibility. Existing synchronous REST calls remain unchanged.

## EVT-020-002 Event Envelope
All events use the shared `learngrid-events` envelope:

| Field | Type | Purpose |
| --- | --- | --- |
| `event_id` | UUID string | Global idempotency key |
| `event_type` | string | Business event name, such as `CoursePublished` |
| `aggregate_id` | UUID string | Primary resource ID for partition keys and tracing |
| `producer_service` | string | Service that emitted the event |
| `timestamp` | ISO-8601 timestamp | Event creation time |
| `version` | integer | Envelope version, currently `1` |
| `correlation_id` | string or null | Optional request/workflow correlation ID |
| `payload` | object | Event-specific data |

## EVT-020-003 Topic Catalog
Base topics:

| Topic | Primary producer |
| --- | --- |
| `audit.events` | `auth-service` |
| `user.events` | `user-service` |
| `course.events` | `course-service` |
| `content.events` | `content-service` |
| `enrollment.events` | `enrollment-service` |
| `progress.events` | `progress-service` |
| `assessment.events` | `assessment-service` |
| `grading.events` | `grading-service` |
| `notification.events` | `notification-service` |
| `analytics.events` | `analytics-service` |

Each base topic also has `<topic>.retry` and `<topic>.dlq` derived topics. Local defaults use three partitions and replication factor one.

## EVT-020-004 Producers
The shared package is located at [backend/shared/learngrid-events](../../backend/shared/learngrid-events). Backend services depend on it as an editable path dependency.

`publish_event(...)` validates the envelope, resolves the service topic, and publishes after database commit through `transaction.on_commit` where possible. If `KAFKA_ENABLED=false`, the event is logged locally and the same envelope is returned for tests and local workflows.

## EVT-020-005 Consumers
Consumer helpers validate envelope shape, pass events to explicit service handlers, and enforce these outcomes:

| Outcome | Behavior |
| --- | --- |
| `processed` | Handler completed successfully |
| `duplicate` | Handler raised `DuplicateEvent`; no retry is scheduled |
| `retry_scheduled` | Handler failed and message is sent to `<topic>.retry` |
| `dead_lettered` | Handler failed beyond max attempts or raised `DeadLetterEventError`; message is sent to `<topic>.dlq` |

Consumer handlers are configured through each service `KAFKA_EVENT_HANDLERS` setting. Implemented handlers include:

| Service | Handler key | Handler |
| --- | --- | --- |
| `analytics-service` | `analytics.event_fact` | `apps.analytics.services.handle_kafka_analytics_event` |
| `notification-service` | `notification.in_app` | `apps.notifications.services.handle_kafka_notification_event` |
| `progress-service` | `progress.assessment` | `apps.progress.services.handle_kafka_progress_event` |

## EVT-020-006 Management Commands
Every Django service includes the shared management commands:

```bash
poetry run python manage.py kafka_consume --topic course.events --group analytics-service-consumer --handler analytics.event_fact
poetry run python manage.py kafka_retry_dlq --topic course.events.dlq --event-id <uuid>
poetry run python manage.py kafka_consumer_lag --group analytics-service-consumer
```

## EVT-020-007 Local Infrastructure
`docker-compose.yml` includes:

| Service | Purpose | Local URL |
| --- | --- | --- |
| `kafka` | Apache Kafka broker | `127.0.0.1:9092` |
| `kafka-init` | One-shot base/retry/DLQ topic bootstrap | N/A |
| `kafka-ui` | Local topic and consumer visibility | `http://127.0.0.1:8090` |

`pnpm dev`, `pnpm dev:fast`, and `pnpm dev:infra` start Kafka with PostgreSQL, Redis, and MinIO.

## EVT-020-008 Tests
Shared package tests cover envelope validation, topic catalog, producer serialization, consumer success, duplicate handling, retry, and DLQ routing. Service tests cover analytics event ingestion, notification event processing, and progress event processing through Kafka handlers.
