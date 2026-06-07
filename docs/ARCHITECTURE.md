# LearnGrid LMS Architecture

Source: [SRD.pdf](SRD.pdf)

## ARCH-001 System Goal
LearnGrid LMS is a web-based learning management platform for institutions, instructors,
administrators, students, teaching assistants, and optional parent or guardian users. The
platform targets approximately 10,000 simultaneous users and production-grade reliability.

## ARCH-002 Stack
- Frontend: React, TypeScript, Tailwind CSS, React Router, TanStack Query, Axios, React Hook Form, Zod.
- Backend: Django, Django REST Framework, split settings, Gunicorn or Uvicorn depending on service needs.
- Database: PostgreSQL, database-per-service, PgBouncer, backups, indexing, optional read replicas.
- Cache and temporary data: Redis.
- Event streaming: Kafka.
- Testing: Pytest, Django Test Framework, DRF API tests, Selenium, contract tests, k6 or Locust.
- Deployment: Docker, Kubernetes, Helm, API Gateway or Nginx Ingress, CI/CD, Prometheus, Grafana, Loki or ELK, Sentry.

## ARCH-003 Services
| Service ID | Service | Database | Primary responsibility | Related specs |
| --- | --- | --- | --- | --- |
| SVC-001 | auth-service | auth_db | Credentials, login, tokens, password reset, auth audit, rate limiting | [SPEC-001](specs/001-authentication-lifecycle.md), [SPEC-002](specs/002-token-session-security.md), [SPEC-003](specs/003-rbac-object-authorization.md) |
| SVC-002 | user-service | user_db | Profiles, institutions, departments, batches, profile search | [SPEC-004](specs/004-user-profile-management.md), [SPEC-005](specs/005-institution-batch-department-management.md) |
| SVC-003 | course-service | course_db | Catalog, metadata, modules, lessons, topics, outcomes | [SPEC-006](specs/006-course-catalog-metadata.md), [SPEC-007](specs/007-course-structure-versioning.md) |
| SVC-004 | content-service | content_db | Content metadata, file upload, signed access, object storage | [SPEC-008](specs/008-content-upload-storage-access.md) |
| SVC-005 | enrollment-service | enrollment_db | Student enrollment, course access, enrollment history | [SPEC-009](specs/009-enrollment-access-management.md) |
| SVC-006 | progress-service | progress_db | Lesson, video, quiz, assignment, and course progress | [SPEC-010](specs/010-learning-progress-tracking.md) |
| SVC-007 | assessment-service | assessment_db | Question banks, quizzes, assignments, attempts, submissions | [SPEC-012](specs/012-assessment-authoring.md), [SPEC-013](specs/013-quiz-attempts-exams.md), [SPEC-014](specs/014-assignment-submissions.md) |
| SVC-008 | grading-service | grading_db | Automatic grading, manual grading, result publishing, audit history | [SPEC-015](specs/015-grading-results-audit.md), [SPEC-016](specs/016-certificates.md) |
| SVC-009 | notification-service | notification_db | In-app notifications, future email/SMS/push, delivery status | [SPEC-017](specs/017-notifications.md) |
| SVC-010 | analytics-service | analytics_db | Dashboards, reports, engagement metrics, usage analytics | [SPEC-018](specs/018-search-reporting-analytics.md) |
| SVC-011 | frontend-service | N/A | React frontend application for student, instructor, and admin portals | [SPEC-011](specs/011-dashboards-portals.md), [SPEC-023](specs/023-ci-cd-deployment-observability.md) |

## ARCH-004 Cross-Service Rules
- Each service owns its database and schema.
- Services must not directly query another service database.
- Cross-service references are stored as UUID fields.
- Synchronous reads use service APIs.
- Asynchronous workflows use Kafka events.
- Consumers must be idempotent and support retry and dead-letter handling.

## ARCH-005 Production Platform
- External traffic uses HTTPS through an API Gateway or ingress.
- Services run as Kubernetes Deployments with multiple replicas where critical.
- Services expose readiness and liveness probes.
- PostgreSQL, Redis, Kafka, and object storage must be production-grade managed or clustered services.
- Metrics, logs, traces, and errors are centralized.

## ARCH-006 Open Decisions
Open platform decisions remain unresolved and are tracked in [KNOWN_ISSUES.md](KNOWN_ISSUES.md):
[OD-001](KNOWN_ISSUES.md#od-001-api-gateway-selection),
[OD-002](KNOWN_ISSUES.md#od-002-object-storage-selection),
[OD-003](KNOWN_ISSUES.md#od-003-deployment-model),
[OD-004](KNOWN_ISSUES.md#od-004-authentication-model),
[OD-005](KNOWN_ISSUES.md#od-005-analytics-storage),
[OD-006](KNOWN_ISSUES.md#od-006-video-delivery-strategy).
