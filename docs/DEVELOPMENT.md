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

The command starts PostgreSQL, Redis, all ten Django backend services, and the Vite frontend.
It also installs dependencies, ensures service databases exist, runs backend migrations, waits
for health endpoints, and streams prefixed logs.

For repeat starts after dependencies and migrations are already prepared:

```bash
pnpm dev:fast
```

`Ctrl+C` stops the backend and frontend processes. PostgreSQL and Redis are left running so
local data is preserved.

Stop local infrastructure:

```bash
pnpm dev:infra:down
```

If Poetry is not installed as `poetry`, pass its path explicitly:

```bash
POETRY_BIN=/path/to/poetry pnpm dev
```

## Local Infrastructure
Start PostgreSQL and Redis:

```bash
pnpm dev:infra
```

PostgreSQL initialization creates these service databases:
`auth_db`, `user_db`, `course_db`, `content_db`, `enrollment_db`, `progress_db`,
`assessment_db`, `grading_db`, `notification_db`, and `analytics_db`.
The run script also checks and creates these databases when an existing Docker volume skipped
the initialization SQL.

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

## Backend Services
Each backend service is a Django REST Framework application with split settings and a public
health endpoint.

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
poetry run python manage.py check
poetry run pytest
poetry run python manage.py runserver 8001
```

## Auth Token Configuration
`auth-service` implements the JWT baseline for [T-002](tasks/T-002-token-session-security.md).

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `AUTH_ACCESS_TOKEN_LIFETIME_SECONDS` | `300` | Access token lifetime, 5 minutes |
| `AUTH_REFRESH_TOKEN_LIFETIME_SECONDS` | `604800` | Refresh token lifetime, 7 days |
| `AUTH_JWT_ISSUER` | `learngrid-auth-service` | JWT issuer claim |
| `AUTH_JWT_SIGNING_KEY` | `DJANGO_SECRET_KEY` | HMAC signing key for access and refresh JWTs |
| `AUTH_TOKEN_HASH_KEY` | `DJANGO_SECRET_KEY` | HMAC key for stored refresh token hashes |
| `AUTH_PERMISSION_CACHE_TTL_SECONDS` | `300` | RBAC permission check cache TTL |

Token blacklist entries are written to Redis with a TTL matching the remaining token lifetime
and are also stored in `auth_db.token_blacklist` for durable fallback.

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

## CI
GitHub Actions runs frontend lint, typecheck, tests, and build. It also runs Ruff, Django checks,
and pytest for each backend service.
