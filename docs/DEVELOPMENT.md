# Development Setup

Related task: [T-001 Project Setup](tasks/T-001-project-setup.md)

## Required Tools
- Node.js 22+
- pnpm 11+
- Python 3.12+
- Poetry 2+
- Docker with Compose

## Run The Full Stack
Start the complete local LearnGrid LMS stack:

```bash
pnpm dev
```

The command starts PostgreSQL, Redis, MinIO, all ten Django backend services, and the Vite
frontend. It also installs dependencies, ensures service databases and the MinIO content bucket
exist, runs backend migrations, waits for health endpoints, and streams prefixed logs.

For repeat starts after dependencies and migrations are already prepared:

```bash
pnpm dev:fast
```

`Ctrl+C` stops the backend and frontend processes. PostgreSQL, Redis, and MinIO are left running
so local data is preserved.

Stop local infrastructure:

```bash
pnpm dev:infra:down
```

If Poetry is not installed as `poetry`, pass its path explicitly:

```bash
POETRY_BIN=/path/to/poetry pnpm dev
```

## Local Infrastructure
Start PostgreSQL, Redis, and MinIO:

```bash
pnpm dev:infra
```

PostgreSQL initialization creates these service databases:
`auth_db`, `user_db`, `course_db`, `content_db`, `enrollment_db`, `progress_db`,
`assessment_db`, `grading_db`, `notification_db`, and `analytics_db`.
The run script also checks and creates these databases when an existing Docker volume skipped
the initialization SQL.

MinIO local defaults:

| Item | Value |
| --- | --- |
| API URL | `http://127.0.0.1:9000` |
| Console URL | `http://127.0.0.1:9001` |
| Root user | `learngrid` |
| Root password | `learngrid-minio-secret` |
| Content bucket | `learngrid-content` |

Redis local defaults:

| Item | Value |
| --- | --- |
| URL | `redis://localhost:6379/0` |
| Key prefix | `lg:{REDIS_ENV}:{service}:...`, default `REDIS_ENV=local` |
| Shared helper package | `backend/shared/learngrid-redis` |
| Production HA | Redis Sentinel through `REDIS_SENTINEL_URLS`, master name `mymaster`, port `26379` |

Redis design details, key naming, TTLs, invalidation, and outage behavior are documented in
[REDIS-021](redis-design/REDIS-021-redis-architecture.md). The T-023 on-prem Kubernetes runtime
chart uses a Sentinel-backed primary/replica topology for production. Local development continues
to use the direct `REDIS_URL` path.

## API Gateway
`T-019` resolves [OD-001](KNOWN_ISSUES.md#od-001-api-gateway-selection) to Nginx.
`pnpm dev` and `pnpm dev:fast` start the gateway after backend and frontend services are healthy.

| Item | Value |
| --- | --- |
| HTTP URL | `http://127.0.0.1:8080` |
| HTTPS URL | `https://127.0.0.1:8443` |
| Health URL | `https://127.0.0.1:8443/gateway/health` |
| TLS helper | `scripts/generate-local-gateway-cert.sh` |

Gateway HTTP redirects to HTTPS. The local HTTPS certificate is self-signed and generated into an
ignored `infrastructure/docker/nginx/certs/` path. Nginx routes `/api/*` prefixes to backend
services, rewrites `/api/v1/...` to `/api/...`, and aliases `/api/grades/...` to
`/api/grading/...`. It also applies request IDs, JSON access logs, local-origin CORS, rate limits,
security headers, and a `20m` request size limit.

## Security Baseline
`T-022` adds shared production security helpers, gateway security headers, stricter validation,
optional malware scanning, Kubernetes security baseline templates, and backup restore verification.

Production settings for every backend service require:

| Environment variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Service-specific Django secret |
| `DATABASE_URL` | Service database connection |
| `DJANGO_ALLOWED_HOSTS` | Production host allowlist |
| `CORS_ALLOWED_ORIGINS` | Browser origin allowlist |
| `CSRF_TRUSTED_ORIGINS` | Trusted origins if cookie auth is selected later |
| `AUTH_JWT_SIGNING_KEY` | JWT verification key for auth-aware services |
| `AUTH_TOKEN_HASH_KEY` | Auth-service token hash key |
| `CONTENT_MINIO_ACCESS_KEY` / `CONTENT_MINIO_SECRET_KEY` | Content object-storage credentials |

Local `.env.example` values are intentionally local-only. `config.settings.production` rejects
missing values and obvious local placeholders such as `insecure-local` or `change-me`.

Content upload security options:

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `CONTENT_ALLOWED_FILE_EXTENSIONS` | `.mp4,.pdf,.doc,.docx,.png,.jpg,.jpeg,.txt` | File extension allowlist |
| `CONTENT_MALWARE_SCAN_ENABLED` | `false` | Enable fail-closed malware scanner hook |
| `CONTENT_MALWARE_SCANNER_COMMAND` | empty | Scanner command invoked with the file path or object key |
| `CONTENT_MALWARE_SCAN_TIMEOUT_SECONDS` | `10` | Scanner timeout |

Backup restore verification:

```bash
docker compose up -d postgres
bash scripts/verify-postgres-backup-restore.sh
```

Security-only Kubernetes templates live under
`infrastructure/kubernetes/security-baseline/`. Full production Deployments, Services, HPAs,
probes, and rollout wiring remain for [T-023](tasks/T-023-ci-cd-deployment-observability.md).

## Frontend Service
The frontend service is `SVC-011 frontend-service`.

```bash
pnpm install
pnpm -C frontend lint
pnpm -C frontend typecheck
pnpm -C frontend test
pnpm -C frontend build
pnpm -C frontend dev
```

Local URL: `http://127.0.0.1:5173`

Implemented portal routes:

| Portal | Routes |
| --- | --- |
| Student | `/dashboard/student`, `/dashboard/student/courses`, `/dashboard/student/courses/:courseId`, `/dashboard/student/courses/:courseId/learn`, `/dashboard/student/progress`, `/dashboard/student/assessments/:assessmentId/attempt`, `/dashboard/student/assignments/:assignmentId/submit`, `/dashboard/student/certificates`, `/dashboard/student/notifications` |
| Instructor | `/dashboard/instructor`, `/dashboard/instructor/courses`, `/dashboard/instructor/courses/:courseId/builder`, `/dashboard/instructor/content`, `/dashboard/instructor/assessments`, `/dashboard/instructor/grading`, `/dashboard/instructor/reports`, `/dashboard/instructor/notifications` |
| Admin | `/dashboard/admin`, `/dashboard/admin/users/new`, `/dashboard/admin/enrollments`, `/dashboard/admin/reports`, `/dashboard/admin/notifications` |

The Vite dev proxy routes all implemented `/api/*` service prefixes to local backend service ports.
Frontend role-aware navigation hides unrelated portal routes, but backend authorization remains
authoritative for every API request.

## Backend Services
Each backend service is a Django REST Framework application with split settings and a public
health endpoint. Production containers use Gunicorn and expose `/health/`, `/health/live/`,
`/health/ready/`, `/metrics/`, `/api/schema/`, and `/api/docs/`.

| Service | Port | Health URL |
| --- | --- | --- |
| auth-service | 8001 | `http://127.0.0.1:8001/health/` |
| user-service | 8002 | `http://127.0.0.1:8002/health/` |
| course-service | 8003 | `http://127.0.0.1:8003/health/` |
| content-service | 8004 | `http://127.0.0.1:8004/health/` |
| enrollment-service | 8005 | `http://127.0.0.1:8005/health/` |
| progress-service | 8006 | `http://127.0.0.1:8006/health/` |
| assessment-service | 8007 | `http://127.0.0.1:8007/health/` |
| grading-service | 8008 | `http://127.0.0.1:8008/health/` |
| notification-service | 8009 | `http://127.0.0.1:8009/health/` |
| analytics-service | 8010 | `http://127.0.0.1:8010/health/` |

Run checks for a service:

```bash
cd backend/services/auth-service
poetry install
poetry run ruff check .
poetry run ruff format --check .
poetry run mypy .
poetry run python manage.py check
poetry run python manage.py makemigrations --check --dry-run
poetry run pytest
poetry run python manage.py runserver 8001
```

## Testing And Quality
Root-level test helpers are installed from `requirements-test.txt`.

```bash
python -m pip install -r requirements-test.txt
python -m pytest tests/contracts
python -m pytest tests/integration
python -m pytest tests/e2e
k6 run tests/load/smoke.js
```

Optional test environment variables:

| Environment variable | Purpose |
| --- | --- |
| `CONTRACT_SERVICE_URLS` | Optional live OpenAPI contract targets as JSON or `service=url` pairs |
| `INTEGRATION_DATABASE_URL` | PostgreSQL URL for Compose-backed integration checks |
| `INTEGRATION_REDIS_URL` | Redis URL for real helper checks |
| `INTEGRATION_KAFKA_BOOTSTRAP_SERVERS` | Kafka bootstrap servers for produce/consume checks |
| `INTEGRATION_MINIO_ENDPOINT` | MinIO endpoint for object storage checks |
| `E2E_BASE_URL` | Browser E2E target URL; tests skip when unset |
| `E2E_*_EMAIL` / `E2E_*_PASSWORD` | Optional student, instructor, and admin credentials |
| `LOAD_BASE_URL` | k6 target URL; smoke script runs offline when unset |
| `LOAD_*_EMAIL` / `LOAD_*_PASSWORD` | Optional k6 role credentials |
| `LOAD_VUS` / `LOAD_DURATION` | k6 virtual users and duration |

GitHub Actions runs backend Ruff, format, mypy, Django checks, migration dry-runs, and pytest;
frontend lint, typecheck, tests, build, and high-severity audit; plus actionlint, shell syntax,
contract, integration, E2E, k6, gateway, security, deployment, image, and Helm checks.

## Deployment And Observability
`T-023` resolves [OD-003](KNOWN_ISSUES.md#od-003-deployment-model) to on-prem Kubernetes.

Helm charts live under `infrastructure/helm/`:

| Chart | Purpose |
| --- | --- |
| `learngrid-platform` | Namespaces and pod-security labels |
| `learngrid-runtime` | CloudNativePG PostgreSQL, MinIO, Strimzi Kafka, Redis, Kafka UI, Prometheus, Grafana, Loki, Tempo, Alloy, and exporters |
| `learngrid-app` | LearnGrid backend, frontend, gateway, ConfigMaps, Secret references, HPAs, probes, migration Jobs, PDBs, Ingress, and NetworkPolicies |

Production runtime variables:

| Environment variable | Purpose |
| --- | --- |
| `PORT` | Container listen port, default `8000` for backend images |
| `GUNICORN_WORKERS` | Backend Gunicorn worker count |
| `GUNICORN_TIMEOUT_SECONDS` | Backend Gunicorn request timeout |
| `SENTRY_DSN` / `VITE_SENTRY_DSN` | Backend/frontend error reporting DSNs |
| `SENTRY_ENVIRONMENT` | Sentry deployment environment |
| `SENTRY_TRACES_SAMPLE_RATE` | Backend Sentry trace sample rate |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP HTTP trace endpoint, typically Tempo |
| `OTEL_SERVICE_NAME` | Service name used for traces |

GitHub Actions builds backend, frontend, and gateway images, scans them with Trivy, pushes GHCR
tags, deploys staging with `KUBE_CONFIG_STAGING`, and deploys production with
`KUBE_CONFIG_PRODUCTION` after the GitHub `production` environment approval gate. Final `T-023.06`
completion requires a successful real staging deployment smoke run.

## Auth Token Configuration
`auth-service` implements the JWT baseline for [T-002](tasks/T-002-token-session-security.md).

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `AUTH_ACCESS_TOKEN_LIFETIME_SECONDS` | `300` | Access token lifetime, 5 minutes |
| `AUTH_REFRESH_TOKEN_LIFETIME_SECONDS` | `604800` | Refresh token lifetime, 7 days |
| `AUTH_JWT_ISSUER` | `learngrid-auth-service` | JWT issuer claim |
| `AUTH_JWT_SIGNING_KEY` | `DJANGO_SECRET_KEY` | HMAC signing key for access and refresh JWTs |
| `AUTH_TOKEN_HASH_KEY` | `DJANGO_SECRET_KEY` | HMAC key for stored refresh token hashes |
| `AUTH_PASSWORD_MIN_LENGTH` | `12` | Minimum temporary/reset password length |
| `AUTH_PERMISSION_CACHE_TTL_SECONDS` | `300` | RBAC permission check cache TTL |
| `AUTH_LOGIN_RATE_LIMIT_COUNT` | `5` | Login attempts allowed per Redis fixed window |
| `AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS` | `900` | Login rate-limit window |
| `AUTH_PASSWORD_RESET_RATE_LIMIT_COUNT` | `3` | Password reset requests allowed per Redis fixed window |
| `AUTH_PASSWORD_RESET_TTL_SECONDS` | `900` | Password reset token Redis TTL and DB expiry |
| `AUTH_OTP_TTL_SECONDS` | `300` | OTP Redis TTL |
| `AUTH_OTP_MAX_ATTEMPTS` | `5` | OTP verification attempts before the key is removed |
| `AUTH_OIDC_ENABLED` | `false` | Enables generic OIDC login |
| `AUTH_OIDC_PROVIDER_LABEL` | `SSO` | Label shown on the frontend SSO button |
| `AUTH_OIDC_ISSUER_URL` | empty | OIDC issuer discovery URL |
| `AUTH_OIDC_CLIENT_ID` | empty | OIDC client ID |
| `AUTH_OIDC_CLIENT_SECRET` | empty | OIDC client secret |
| `AUTH_OIDC_REDIRECT_URI` | frontend callback URL | Redirect URI registered with the provider |
| `AUTH_OIDC_SCOPES` | `openid email profile` | Requested scopes |
| `AUTH_OIDC_REQUIRE_EMAIL_VERIFIED` | `true` | Reject unverified provider email claims |
| `AUTH_OIDC_STATE_TTL_SECONDS` | `300` | Redis TTL for state, nonce, and PKCE verifier |
| `AUTH_OIDC_JWKS_CACHE_TTL_SECONDS` | `3600` | Redis TTL for provider discovery/JWKS cache |

Token blacklist entries are written to Redis with a TTL matching the remaining token lifetime
and are also stored in `auth_db.token_blacklist` for durable fallback.
Login and password reset endpoints use Redis-backed fixed-window rate limits. Password reset raw
tokens are stored only as hashes in PostgreSQL and as hashed Redis keys.

Password reset APIs:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/password-reset/request/` | Request a reset token; always returns `{"status":"accepted"}` |
| `POST` | `/api/auth/password-reset/confirm/` | Confirm a reset token and set a new password |

OIDC APIs:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/auth/oidc/config/` | Report whether SSO is enabled and expose the provider label |
| `POST` | `/api/auth/oidc/authorize/` | Create state/nonce/PKCE values and return the provider authorization URL |
| `POST` | `/api/auth/oidc/callback/` | Validate provider callback, link to an existing active account, and return the standard token pair |

OIDC does not provision users. Admins must create accounts, profiles, and roles before SSO can
match a verified provider email or an existing `issuer + subject` link.

## RBAC And Object Authorization
`auth-service` implements the RBAC baseline for [T-003](tasks/T-003-rbac-object-authorization.md).

RBAC APIs:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/auth/rbac/roles/` | List seeded roles |
| `GET` | `/api/auth/rbac/permissions/` | List permission catalog |
| `POST` | `/api/auth/rbac/role-assignments/` | Assign a role at platform, institution, course, or assessment scope |
| `DELETE` | `/api/auth/rbac/role-assignments/<uuid>/` | Revoke a role assignment |
| `POST` | `/api/auth/authorization/check/` | Check the current access token against a permission and scope |

Non-auth services validate JWTs locally and call `auth-service` for permission checks. Configure:

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `AUTH_SERVICE_BASE_URL` | `http://127.0.0.1:8001` | Auth-service URL used for authorization checks |
| `AUTH_JWT_SIGNING_KEY` | `insecure-local-auth-service-change-me-32bytes` | Shared JWT signing key for local token validation |
| `AUTH_JWT_ISSUER` | `learngrid-auth-service` | Expected JWT issuer |
| `AUTH_JWT_ALGORITHM` | `HS256` | JWT signing algorithm |

Authorization failures deny by default. The permission cache is invalidated after role assignment
and role-permission changes.

## User And Profile Management
`user-service` implements the first profile workflow for
[T-004](tasks/T-004-user-profile-management.md). Auth-service remains the only writer for
authentication accounts; user-service creates, updates, and deactivates auth accounts through
auth-service APIs and owns profile/institution lifecycle data in `user_db`.

Auth account APIs:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/accounts/` | Create an active account with a temporary password and optional initial role assignment |
| `PATCH` | `/api/auth/accounts/<uuid>/` | Update account email, phone, or status |
| `POST` | `/api/auth/accounts/<uuid>/deactivate/` | Deactivate an account and revoke active tokens |

User profile APIs:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/users/profiles/` | Create auth account, base profile, and student/instructor/admin profile |
| `GET` | `/api/users/profiles/` | Search profiles with `institution_id`, `q`, `profile_type`, `status`, `department_id`, `batch_id`, `sort`, `page`, and `page_size` |
| `GET` | `/api/users/profiles/<uuid>/` | Read a profile with role-specific profile data |
| `PATCH` | `/api/users/profiles/<uuid>/` | Update local profile fields and optional auth account email/phone |
| `POST` | `/api/users/profiles/<uuid>/deactivate/` | Deactivate the profile and auth account together |
| `POST` | `/api/users/import-jobs/` | Future bulk-import placeholder returning `501 not_implemented` |

Profile APIs require `profile.view` or `profile.manage` through the T-003 remote authorization
helper. Requests with an `institution_id` use institution scope; requests without one use platform
scope. If local profile creation fails after auth account creation, user-service calls auth-service
deactivation as compensation.

## Institution, Department, And Batch Management
`user-service` implements organization management for
[T-005](tasks/T-005-institution-batch-department-management.md). The APIs use the existing
`institutions`, `departments`, and `batches` tables in `user_db`.

Organization APIs:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/users/institutions/` | Search institutions with `q`, `status`, `sort`, `page`, and `page_size` |
| `POST` | `/api/users/institutions/` | Create an institution |
| `GET` | `/api/users/institutions/<uuid>/` | Read an institution |
| `PATCH` | `/api/users/institutions/<uuid>/` | Update an institution |
| `DELETE` | `/api/users/institutions/<uuid>/` | Soft-delete an institution |
| `GET` | `/api/users/departments/` | Search departments with `institution_id`, `q`, `status`, `sort`, `page`, and `page_size` |
| `POST` | `/api/users/departments/` | Create a department inside an institution |
| `GET` | `/api/users/departments/<uuid>/` | Read a department |
| `PATCH` | `/api/users/departments/<uuid>/` | Update a department |
| `DELETE` | `/api/users/departments/<uuid>/` | Soft-delete a department |
| `GET` | `/api/users/batches/` | Search batches with `institution_id`, `department_id`, `q`, `status`, `sort`, `page`, and `page_size` |
| `POST` | `/api/users/batches/` | Create a batch inside an institution |
| `GET` | `/api/users/batches/<uuid>/` | Read a batch |
| `PATCH` | `/api/users/batches/<uuid>/` | Update a batch |
| `DELETE` | `/api/users/batches/<uuid>/` | Soft-delete a batch |

Institution endpoints require `institution.manage` at platform scope. Department and batch
endpoints require `institution.manage` at the target institution scope. `DELETE` archives records
by setting `status = archived` and `deleted_at`; historical foreign key relationships are preserved.
Organization codes are normalized to uppercase and remain reserved after soft delete.

## Course Catalog And Metadata
`course-service` implements catalog metadata for
[T-006](tasks/T-006-course-catalog-metadata.md). It owns the implemented `course_db`
tables for courses, categories, tags, prerequisites, and learning outcomes.

Course APIs:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/courses/` | Search courses with `institution_id`, `owner_profile_id`, `status`, `difficulty_level`, `category_id`, `tag_id`, `q`, `sort`, `page`, and `page_size` |
| `POST` | `/api/courses/` | Create a draft course with optional categories, tags, prerequisites, and learning outcomes |
| `GET` | `/api/courses/<uuid>/` | Read one course |
| `PATCH` | `/api/courses/<uuid>/` | Update course fields and replace supplied metadata arrays |
| `POST` | `/api/courses/<uuid>/publish/` | Publish a course |
| `POST` | `/api/courses/<uuid>/archive/` | Archive a course |
| `DELETE` | `/api/courses/<uuid>/` | Soft-delete a course by setting `status = deleted` and `deleted_at` |

Course create/update payload fields include `institution_id`, `owner_profile_id`, `title`,
optional `slug`, `description`, `difficulty_level`, `thumbnail_asset_id`, `category_ids`,
`tag_ids`, `prerequisite_course_ids`, and ordered `learning_outcomes`. Slugs are normalized
to lowercase URL-safe values and generated from the title when omitted.

Category and tag APIs:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/courses/categories/` | Search categories with `institution_id`, `q`, `sort`, `page`, and `page_size` |
| `POST` | `/api/courses/categories/` | Create a global or institution-scoped category |
| `GET` | `/api/courses/categories/<uuid>/` | Read one category |
| `PATCH` | `/api/courses/categories/<uuid>/` | Update category name, slug, or parent |
| `DELETE` | `/api/courses/categories/<uuid>/` | Delete a category and its links |
| `GET` | `/api/courses/tags/` | Search tags with `institution_id`, `q`, `sort`, `page`, and `page_size` |
| `POST` | `/api/courses/tags/` | Create a global or institution-scoped tag |
| `GET` | `/api/courses/tags/<uuid>/` | Read one tag |
| `PATCH` | `/api/courses/tags/<uuid>/` | Update tag name or slug |
| `DELETE` | `/api/courses/tags/<uuid>/` | Delete a tag and its links |

Course writes and lifecycle actions require `course.manage` at the course institution.
Published catalog reads require `course.view`; draft, archived, and deleted reads require
`course.manage`. Category and tag writes require `course.manage`; global records use
platform scope and institution records use institution scope. Auth-service denial or network
failure denies access.

Published catalog list/detail responses are cached in Redis for
`COURSE_CATALOG_CACHE_TTL_SECONDS`, default `300`. Management and non-published reads bypass
cache. Course, category, tag, prerequisite, and learning outcome writes invalidate catalog
cache keys. Catalog cache keys hash raw query parameters, and Redis failures fall back to
database reads. Course/module/lesson/topic reorder writes use Redis distributed locks with
`REDIS_LOCK_TTL_SECONDS`, default `30`; lock contention or Redis outage returns `409`.

Course lifecycle emits `CourseCreated`, `CoursePublished`, and `CourseArchived` through the
shared Kafka-capable event publisher described in [EVT-020](event-design/EVT-020-kafka-eventing.md).
When `KAFKA_ENABLED=false`, the same envelope is logged locally.

## Kafka Eventing
`pnpm dev`, `pnpm dev:fast`, and `pnpm dev:infra` start Apache Kafka with the local stack.

| Component | Local endpoint |
| --- | --- |
| Kafka broker | `127.0.0.1:9092` |
| Kafka UI | `http://127.0.0.1:8090` |

Kafka settings:

| Variable | Default | Purpose |
| --- | --- | --- |
| `KAFKA_ENABLED` | `true` from `scripts/run-dev.sh` | Enables real Kafka publishing for local app processes |
| `KAFKA_BOOTSTRAP_SERVERS` | `127.0.0.1:9092` | Broker bootstrap address |
| `KAFKA_DEFAULT_PARTITIONS` | `3` | Topic partitions used by `kafka-init` |
| `KAFKA_REPLICATION_FACTOR` | `1` | Local topic replication factor |
| `KAFKA_CONSUMER_GROUP` | `<service-name>-consumer` | Default consumer group per service |
| `KAFKA_MAX_RETRY_ATTEMPTS` | `3` | Attempts before DLQ routing |

Kafka management commands are available in every Django service through the shared
`learngrid-events` app:

```bash
poetry run python manage.py kafka_consume --topic course.events --group analytics-service-consumer --handler analytics.event_fact
poetry run python manage.py kafka_retry_dlq --topic course.events.dlq --event-id <uuid>
poetry run python manage.py kafka_consumer_lag --group analytics-service-consumer
```

Implemented consumer handlers:

| Service | Handler key | Typical topics |
| --- | --- | --- |
| `analytics-service` | `analytics.event_fact` | All base topics |
| `notification-service` | `notification.in_app` | `enrollment.events`, `progress.events`, `grading.events` |
| `progress-service` | `progress.assessment` | `assessment.events` |

## Course Structure And Versioning
`course-service` implements ordered course structure for
[T-007](tasks/T-007-course-structure-versioning.md). It owns `course_modules`, `lessons`,
`topics`, and `course_revisions` in `course_db`.

Structure APIs:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/courses/<uuid>/structure/` | Read nested modules, lessons, and topics |
| `GET` | `/api/courses/<uuid>/modules/` | List modules in a course |
| `POST` | `/api/courses/<uuid>/modules/` | Create a module |
| `GET` | `/api/courses/modules/<uuid>/` | Read a module |
| `PATCH` | `/api/courses/modules/<uuid>/` | Update a module |
| `DELETE` | `/api/courses/modules/<uuid>/` | Soft-archive a module |
| `POST` | `/api/courses/<uuid>/modules/reorder/` | Reorder all active modules |
| `GET` | `/api/courses/modules/<uuid>/lessons/` | List lessons in a module |
| `POST` | `/api/courses/modules/<uuid>/lessons/` | Create a lesson |
| `GET` | `/api/courses/lessons/<uuid>/` | Read a lesson |
| `PATCH` | `/api/courses/lessons/<uuid>/` | Update a lesson or move it within the same course |
| `DELETE` | `/api/courses/lessons/<uuid>/` | Soft-archive a lesson |
| `POST` | `/api/courses/lessons/<uuid>/publish/` | Publish a lesson and emit `LessonPublished` |
| `POST` | `/api/courses/modules/<uuid>/lessons/reorder/` | Reorder all active lessons in a module |
| `GET` | `/api/courses/lessons/<uuid>/topics/` | List topics in a lesson |
| `POST` | `/api/courses/lessons/<uuid>/topics/` | Create a topic |
| `GET` | `/api/courses/topics/<uuid>/` | Read a topic |
| `PATCH` | `/api/courses/topics/<uuid>/` | Update a topic |
| `DELETE` | `/api/courses/topics/<uuid>/` | Delete a topic |
| `POST` | `/api/courses/lessons/<uuid>/topics/reorder/` | Reorder all topics in a lesson |
| `GET` | `/api/courses/<uuid>/revisions/` | List course revision snapshots |
| `POST` | `/api/courses/<uuid>/revisions/` | Create a course structure snapshot |
| `GET` | `/api/courses/revisions/<uuid>/` | Read one revision snapshot |

Module payload fields are `title`, `description`, optional `position`, and optional `status`.
Lesson payload fields are `title`, `summary`, optional `position`, optional `status`, and
optional `content_asset_id`; update also accepts `module_id` for moving within the same course.
Topic payload fields are `title`, optional `position`, and optional `content_asset_id`.
Reorder requests use `module_ids`, `lesson_ids`, or `topic_ids` and must include the complete
active set for that scope.

Structure writes require `course.manage` at the course institution. Published structure reads
require `course.view` and hide draft lessons plus non-published modules. Management reads include
draft, published, and archived active structure records. Course structure writes invalidate the
published catalog cache.

## Content Upload, Storage, And Access
`content-service` implements [T-008](tasks/T-008-content-upload-storage-access.md) under
`/api/content/`. [OD-002](KNOWN_ISSUES.md#od-002-object-storage-selection) selects MinIO as the
object storage provider. Asset metadata registration validates that the MinIO object exists.
Presigned uploads use `POST /api/content/assets/uploads/presigned/` and
`POST /api/content/assets/<uuid>/uploads/complete/`; backend proxy uploads use
`POST /api/content/assets/uploads/proxy/`. Signed access creates hashed one-time token records,
then `/api/content/download/<uuid>/?token=...` returns a short-lived MinIO presigned GET URL.
Publish and delete emit `ContentPublished` and `ContentDeleted`; upload completion emits
`ContentUploaded`.

## Enrollment And Access Management
`enrollment-service` implements [T-009](tasks/T-009-enrollment-access-management.md) under
`/api/enrollments/`. It supports individual enrollments, batch and cohort enrollment jobs,
status transitions, history reads, and `GET /api/enrollments/access/check/`. Enrollment changes
synchronize derived access grants and emit local `StudentEnrolled`, `StudentRemovedFromCourse`,
and `CourseAccessExpired` events.

## Learning Progress Tracking
`progress-service` implements [T-010](tasks/T-010-learning-progress-tracking.md) under
`/api/progress/`. It supports lesson, video, and assessment progress updates, course progress
reads, and idempotent event ingestion for `LessonViewed`, `VideoCompleted`, `QuizSubmitted`, and
`AssignmentSubmitted`. Optional `total_lessons` and `total_assessments` provide course completion
denominators until cross-service course aggregate reads are added.

## Dashboards And Portals
`frontend-service`, `auth-service`, `user-service`, and `analytics-service` implement
[T-011](tasks/T-011-dashboards-portals.md). The frontend stores the baseline access/refresh token
pair in `localStorage`, attaches bearer tokens through the Axios client, and routes users by the
`primary_role` returned from `GET /api/auth/session/`.

Frontend routes:

| Route | Purpose |
| --- | --- |
| `/login` | Sign in and store token pair |
| `/auth/oidc/callback` | Complete SSO callback, store token pair, and redirect by role |
| `/dashboard` | Load session/profile context and redirect by role |
| `/dashboard/student` | Student dashboard |
| `/dashboard/instructor` | Instructor dashboard |
| `/dashboard/admin` | Admin dashboard |
| `/dashboard/no-access` | Unsupported role fallback |

Vite proxies local API calls to:

| Prefix | Target |
| --- | --- |
| `/api/auth` | `http://127.0.0.1:8001` |
| `/api/users` | `http://127.0.0.1:8002` |
| `/api/analytics` | `http://127.0.0.1:8010` |

Dashboard APIs:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/users/profiles/me/` | Resolve the current profile from the access token |
| `GET` | `/api/analytics/dashboards/student/` | Current student dashboard |
| `GET` | `/api/analytics/dashboards/instructor/` | Current instructor dashboard |
| `GET` | `/api/analytics/dashboards/admin/?institution_id=<uuid>` | Institution dashboard |
| `GET` | `/api/analytics/dashboards/admin/system/` | Platform dashboard |
| `POST` | `/api/analytics/events/ingest/` | Idempotently store analytics event facts |
| `GET/POST` | `/api/analytics/reports/snapshots/` | List or create report snapshots |

Student/instructor dashboards derive the current profile from the bearer token and never accept
arbitrary profile IDs. Admin dashboards require `analytics.view` at institution or platform scope.
If no dashboard aggregate exists, analytics-service returns `200` with empty arrays and zeroed
summary values. PostgreSQL `analytics_db` is the dashboard/report store selected by
[OD-005](KNOWN_ISSUES.md#od-005-analytics-storage).
Dashboard responses are cached in Redis for `ANALYTICS_DASHBOARD_CACHE_TTL_SECONDS`, default
`60`. Dashboard aggregate upserts invalidate matching scope cache keys, and Redis failures fall
back to PostgreSQL reads.

## Search, Reporting, And Analytics
`analytics-service` implements [T-018](tasks/T-018-search-reporting-analytics.md) under
`/api/analytics/`. [OD-005](KNOWN_ISSUES.md#od-005-analytics-storage) is resolved to PostgreSQL
`analytics_db` for the implemented reporting and search scope.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/analytics/search/` | Search all permitted resource types |
| `GET` | `/api/analytics/search/courses/` | Search courses |
| `GET` | `/api/analytics/search/users/` | Search users |
| `GET` | `/api/analytics/search/enrollments/` | Search enrollments |
| `GET` | `/api/analytics/search/assessments/` | Search assessments |
| `GET` | `/api/analytics/search/submissions/` | Search submissions |
| `POST` | `/api/analytics/search/index-records/` | Upsert an analytics search index record |
| `DELETE` | `/api/analytics/search/index-records/<resource_type>/<uuid>/` | Delete an analytics search index record |
| `GET/POST` | `/api/analytics/dashboards/aggregates/` | List or upsert dashboard aggregate records |
| `GET/POST` | `/api/analytics/usage-metrics/` | List or create usage metrics |
| `POST` | `/api/analytics/reports/generate/` | Generate and save a report snapshot |

Search filters: `q`, `institution_id`, `resource_type`, `status`, `course_id`, `profile_type`,
`assessment_type`, `submission_status`, `sort`, `page`, and `page_size`. Generated report types:
`active_users`, `enrollments`, `completion_rates`, `assessment_results`, and `system_usage`.
Report generation reads only analytics-service tables and does not join transactional service
databases.

## Assessment Authoring And Quiz Attempts
`assessment-service` implements [T-012](tasks/T-012-assessment-authoring.md) and
[T-013](tasks/T-013-quiz-attempts-exams.md) under `/api/assessments/`.

Authoring APIs:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET/POST` | `/api/assessments/question-banks/` | Search or create question banks |
| `GET/PATCH/DELETE` | `/api/assessments/question-banks/<uuid>/` | Read, update, or soft-delete a question bank |
| `GET/POST` | `/api/assessments/question-banks/<uuid>/questions/` | Search or create questions |
| `GET/PATCH/DELETE` | `/api/assessments/questions/<uuid>/` | Read, update, or soft-delete a question |
| `GET/POST` | `/api/assessments/` | Search or create quizzes, exams, and assignment shells |
| `GET/PATCH/DELETE` | `/api/assessments/<uuid>/` | Read, update, or archive an assessment |
| `PUT` | `/api/assessments/<uuid>/questions/` | Replace ordered quiz/exam questions |
| `POST` | `/api/assessments/<uuid>/publish/` | Publish and emit `AssessmentPublished` |
| `POST` | `/api/assessments/<uuid>/close/` | Close and emit `AssessmentClosed` |

Question types currently accepted are `multiple_choice`, `multiple_select`, `true_false`,
`short_answer`, `essay`, and `file_upload`. `coding` is reserved in the schema and returns a
validation error. Student-facing attempt responses omit `correct_answer`.

Attempt APIs:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/assessments/<uuid>/attempts/start/` | Start a quiz/exam attempt |
| `GET` | `/api/assessments/attempts/<uuid>/` | Read attempt status, answers, ordered questions, and deadline |
| `PUT` | `/api/assessments/attempts/<uuid>/answers/` | Save answer payloads durably |
| `POST` | `/api/assessments/attempts/<uuid>/submit/` | Submit and emit `QuizSubmitted` |
| `POST` | `/api/assessments/attempts/<uuid>/auto-submit/` | Mark an attempt auto-submitted |

Authoring checks `assessment.manage` at course scope first and then institution scope after
course metadata is resolved from course-service. Student attempts require `assessment.view`, the
current profile from user-service, and active course access from enrollment-service. Quiz answers
are stored in PostgreSQL; Redis is not required for this baseline.

Assignment submission APIs:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET/POST` | `/api/assessments/assignments/<uuid>/submissions/` | List submissions or save a student draft/final submission |
| `GET/PATCH` | `/api/assessments/submissions/<uuid>/` | Read or update an own draft submission |
| `POST` | `/api/assessments/submissions/<uuid>/submit/` | Finalize an assignment submission |
| `POST` | `/api/assessments/submissions/<uuid>/mark-graded/` | Mark a submission graded after grade publication |
| `GET` | `/api/assessments/grading/quiz-attempts/<uuid>/` | Return grading-safe quiz attempt data |
| `GET` | `/api/assessments/grading/assignment-submissions/<uuid>/` | Return grading-safe assignment submission data |

Assignment submissions accept `submission_text`, optional `attachment_asset_id`, and optional
`submit`. Attachment UUIDs are validated through content-service. Final submission enforces the
published assignment status, assessment availability window, due date, late policy, current
student profile, and active enrollment. `AssignmentSubmitted` is emitted locally when a draft or
new submission is finalized.

## Grading, Results, And Audit
`grading-service` implements [T-015](tasks/T-015-grading-results-audit.md) under `/api/grading/`.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET/POST` | `/api/grading/rules/` | List or create grading rules |
| `GET/PATCH` | `/api/grading/rules/<uuid>/` | Read or update one grading rule |
| `GET` | `/api/grading/records/` | List grade records |
| `GET` | `/api/grading/records/<uuid>/` | Read one grade record with history and reviews |
| `POST` | `/api/grading/records/calculate/` | Calculate objective quiz grades from assessment-service source data |
| `POST` | `/api/grading/records/manual-reviews/` | Create a manual review for a quiz attempt or assignment submission |
| `POST` | `/api/grading/manual-reviews/<uuid>/complete/` | Complete a manual review with score and feedback |
| `POST` | `/api/grading/records/<uuid>/override/` | Override a grade with required `change_reason` |
| `POST` | `/api/grading/records/<uuid>/publish/` | Publish a grade result |
| `GET` | `/api/grading/results/` | List published results |
| `GET` | `/api/grading/results/<uuid>/` | Read one published result |
| `GET` | `/api/grading/certificates/eligibility/` | List certificate eligibility records |
| `GET` | `/api/grading/certificates/eligibility/<uuid>/` | Read one eligibility record |
| `POST` | `/api/grading/certificates/eligibility/evaluate/` | Evaluate eligibility and auto-issue when eligible |
| `GET` | `/api/grading/certificates/` | List certificates |
| `GET/PATCH` | `/api/grading/certificates/<uuid>/` | Read a certificate or update `certificate_asset_id` |
| `POST` | `/api/grading/certificates/<uuid>/revoke/` | Revoke a certificate |

Grading APIs use `grade.view` and `grade.manage` through auth-service authorization checks after
resolving course scope from course-service. Automated quiz grading consumes durable attempt scores
from assessment-service. Manual review completion and overrides write immutable grade history.
Publishing creates a student-visible result snapshot, emits `GradePublished`, and asks
assessment-service to mark assignment submissions graded where applicable. Notification-service
consumes `GradePublished` through [T-017](tasks/T-017-notifications.md); external email, SMS, and
push delivery remain future scope.

Certificate eligibility requires completed course progress from progress-service and passing
published grades. The default pass threshold is `GRADING_CERTIFICATE_DEFAULT_PASS_PERCENT=70`,
overridden by course-level grading rule `configuration.certificate_min_percent` when present.
Eligible evaluations auto-issue certificates with numbers formatted as `LG-YYYYMMDD-XXXXXXXXXX`
and emit `CertificateEligible`. Certificate assets are optional UUID references validated through
content-service; certificate PDF generation remains outside this task.

## Notifications
`notification-service` implements [T-017](tasks/T-017-notifications.md) under `/api/notifications/`.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET/POST` | `/api/notifications/templates/` | List or upsert templates |
| `GET/PATCH` | `/api/notifications/templates/<uuid>/` | Read or update one template |
| `GET` | `/api/notifications/` | List notifications for the current profile or scoped admin filter |
| `GET` | `/api/notifications/<uuid>/` | Read one notification |
| `POST` | `/api/notifications/<uuid>/read/` | Mark one notification read |
| `POST` | `/api/notifications/<uuid>/unread/` | Mark one notification unread |
| `POST` | `/api/notifications/read-all/` | Mark current profile notifications read |
| `GET/POST` | `/api/notifications/preferences/` | List or upsert user notification preferences |
| `GET` | `/api/notifications/delivery-attempts/` | List delivery attempts |
| `POST` | `/api/notifications/events/ingest/` | Idempotently process notification events |

Supported event types are `StudentEnrolled`, `AssignmentDueSoon`, `GradePublished`, and
`CourseCompleted`. Events include `event_id`, `event_type`, `aggregate_id`, optional
`producer_service`, optional `timestamp`, and `payload`. In-app notifications are created for
`payload.student_profile_id` or `payload.recipient_profile_ids`, unless the recipient disabled that
event/channel preference. Email, SMS, and push are represented as template/preference channel
placeholders; delivery remains future scope.

## CI
GitHub Actions runs frontend lint, typecheck, tests, and build. It also runs Ruff, Django checks,
and pytest for each backend service.
