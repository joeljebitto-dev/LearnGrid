# HARD-026 Eventing And Async Workflows

Related task: [T-026](../tasks/T-026-backend-hardening-api-completion.md)
Related design: [EVT-020](../event-design/EVT-020-kafka-eventing.md)
Shared package: [learngrid-events](../../backend/shared/learngrid-events)

## HARD-026-EVT-001 Topic Coverage

| Service | Producer topic | Representative events |
| --- | --- | --- |
| `auth-service` | `audit.events` | Security/audit lifecycle events |
| `user-service` | `user.events` | Profile and account lifecycle events |
| `course-service` | `course.events` | `CourseCreated`, `CoursePublished`, `CourseArchived`, lesson lifecycle events |
| `content-service` | `content.events` | Asset upload, publish, delete, and access events |
| `enrollment-service` | `enrollment.events` | Enrollment creation, transition, grants, and batch/cohort events |
| `progress-service` | `progress.events` | Lesson/video/assessment progress and course completion events |
| `assessment-service` | `assessment.events` | Assessment publish/close, quiz attempt, quiz submit, assignment submit events |
| `grading-service` | `grading.events` | Grade calculation/publication and certificate eligibility events |
| `notification-service` | `notification.events` | Notification creation, read state, preference, delivery processing events |
| `analytics-service` | `analytics.events` | Event ingestion, report generation, aggregate/usage metric events |

Every base topic has `<topic>.retry` and `<topic>.dlq` derived topics created by the local Kafka
init service.

## HARD-026-EVT-002 Consumer Coverage

| Consumer service | Base topics | Idempotency rule | Retry/DLQ behavior |
| --- | --- | --- | --- |
| `analytics-service` | All base topics | `event_facts.event_id` is unique and duplicate events are ignored | Shared consumer helper retries retryable failures and DLQs poison messages |
| `notification-service` | Enrollment, progress, grading, course events | Event ingestion records source event IDs and creates retry-safe delivery attempts | Shared consumer helper routes exhausted messages to DLQ |
| `progress-service` | Assessment events | Progress event IDs are durable and duplicate assessment events raise duplicate handling | Shared consumer helper can replay from DLQ through `kafka_retry_dlq` |

## HARD-026-EVT-003 Background Workflow Runbook

| Workflow | Command or owner | Notes |
| --- | --- | --- |
| Kafka consumers | `python manage.py kafka_consume --topic <topic> --group <group> --handler <handler-name>` | Handler maps live in service settings; consumers are explicit per service |
| DLQ replay | `python manage.py kafka_retry_dlq --topic <topic>.dlq --event-id <uuid>` | Replays one event after remediation |
| Lag visibility | `python manage.py kafka_consumer_lag --group <group>` | Returns JSON lag for configured topics and partitions |
| User imports | `user-service` import job records | Placeholder API records jobs; processing remains future bulk workflow scope |
| Notification processing | `notification-service` event ingestion and delivery attempts | Dispatch is retry-safe and preference/template-aware |
| Analytics reports | `analytics-service` report snapshot APIs | Reports are generated from `analytics_db` only; no cross-service database joins |
| Maintenance jobs | Service-specific management commands and runbooks | Use single-service transactions and explicit idempotency keys |

## HARD-026-EVT-004 Test Evidence

- [test_kafka_contracts.py](../../tests/contracts/test_kafka_contracts.py) verifies service topic
  mapping, retry topic naming, DLQ topic naming, and representative event envelopes.
- `learngrid-events` package tests cover envelope validation, producer serialization, duplicate,
  retry, DLQ, and lag helper behavior.
