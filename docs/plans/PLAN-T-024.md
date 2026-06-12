# T-024 Testing And Quality Plan

## Summary
Implement a repo-wide testing and quality baseline that makes unit/API/integration/contract/E2E/load checks documented, runnable, and wired into CI. Use `k6` for load testing. Keep the real production-readiness performance gate open until a staging/on-prem run proves p95 latency, error rate, throughput, PostgreSQL connections, Redis memory, Kafka lag, CPU, memory, and autoscaling behavior.

## Key Changes
- Expand backend test coverage in every service for models, serializers, selectors, services, permissions, happy-path APIs, validation failures, auth failures, object-scope denials, and transaction/audit side effects.
- Add OpenAPI support to every backend service with `drf-spectacular`: expose `/api/schema/` and `/api/docs/`, configure `DEFAULT_SCHEMA_CLASS`, annotate custom `APIView` methods with existing serializers, and add schema smoke tests.
- Add contract tests under `tests/contracts/`:
  - API contracts validate generated OpenAPI JSON for all services, required paths, auth requirements, and stable request/response fields.
  - Kafka contracts validate `learngrid-events` envelopes, topic names, retry/DLQ topics, required event fields, and representative emitted payloads from course/progress/assessment/grading/notification/analytics flows.
- Add integration tests under `tests/integration/` using the existing Docker Compose stack:
  - PostgreSQL migration/smoke checks for each service database.
  - Real Redis cache/rate-limit/lock checks through `learngrid-redis`.
  - Real Kafka produce/consume/retry/DLQ checks through `learngrid-events`.
  - Real MinIO upload/stat/presigned access checks for content storage.
- Replace the current minimal Selenium setup with page objects plus journey tests for student, instructor, admin, course creation/publishing, enrollment, lesson viewing, quiz attempt, assignment submission, grade viewing, RBAC denial, and logout. Tests skip cleanly unless `E2E_BASE_URL` and role credentials are present.
- Add k6 load scripts under `tests/load/` for login, dashboard, course listing, lesson access, quiz submission, and notifications. Include smoke defaults for CI and staging defaults with p95 `<300ms` for common APIs.
- Strengthen CI:
  - Backend: `ruff check`, `ruff format --check`, `mypy`, Django check, migration dry-run, pytest.
  - Frontend: existing lint/typecheck/test/build plus `pnpm audit --audit-level high`.
  - Repo quality: actionlint, shell syntax, `git diff --check`, contract tests, integration tests, E2E smoke, k6 smoke, and existing security/deployment/image checks.
  - Add a root test requirements file for repo-level pytest utilities (`pytest`, `requests`, `jsonschema`, `pyyaml`, `selenium`).

## Public Interfaces
- New backend endpoints for every service:
  - `GET /api/schema/` returns OpenAPI JSON.
  - `GET /api/docs/` returns Swagger UI backed by the service schema.
- New test commands:
  - `python -m pytest tests/contracts`
  - `python -m pytest tests/integration`
  - `python -m pytest tests/e2e`
  - `k6 run tests/load/smoke.js`
  - `k6 run tests/load/staging.js`
- New optional environment variables:
  - `CONTRACT_SERVICE_URLS` for live API contract checks.
  - `INTEGRATION_DATABASE_URL`, `INTEGRATION_REDIS_URL`, `INTEGRATION_KAFKA_BOOTSTRAP_SERVERS`, `INTEGRATION_MINIO_ENDPOINT`.
  - Existing `E2E_*` credentials remain the Selenium credential interface.
  - `LOAD_BASE_URL`, `LOAD_*_EMAIL`, `LOAD_*_PASSWORD`, `LOAD_VUS`, `LOAD_DURATION`.

## Test Plan
- Run all changed backend services: `poetry lock`, `poetry run ruff check .`, `poetry run ruff format --check .`, `poetry run mypy .`, `poetry run python manage.py check`, `poetry run python manage.py makemigrations --check --dry-run`, `poetry run pytest`.
- Run shared packages: Ruff, format check, pytest, and type checks where configured.
- Run frontend: `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`, `pnpm audit --audit-level high`.
- Run repo-level checks: gateway/security/deployment tests, new contract tests, new integration tests with Compose infra, Selenium smoke where credentials exist, k6 smoke, actionlint, shell syntax, Helm validation, image builds/scans, backup restore check, and `git diff --check`.
- Remove generated `__pycache__` artifacts before final verification.

## Task State And Assumptions
- Mark `T-024.01` through `T-024.07` complete after implementation and local/CI verification.
- Leave `T-024.08` unchecked with a note that final performance and autoscaling verification requires a real staging/on-prem run.
- Use Docker Compose for v1 integration tests because the repo already defines PostgreSQL, Redis, Kafka, and MinIO there; do not add Testcontainers unless Compose proves insufficient.
- Do not change product behavior except adding OpenAPI documentation endpoints and test-only harnesses.
