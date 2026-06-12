# Testing Strategy

Source: [SRD.pdf](SRD.pdf)

## TEST-001 Scope
Testing covers unit, API, integration, contract, browser end-to-end, load, security, and deployment smoke tests.

## TEST-002 Unit Tests
- Test models, services, selectors, permissions, and serializers.
- Test business logic independently from API views where possible.
- Use Pytest and Django Test Framework.

## TEST-003 API Tests
- Cover authentication, permissions, validation, happy paths, and failure paths.
- Include object-level authorization tests for protected resources.
- Include pagination, filtering, and sorting tests for list endpoints.
- Every backend service exposes `GET /api/schema/` and `GET /api/docs/` through
  `drf-spectacular`; service tests smoke-check schema JSON and Swagger UI.

## TEST-004 Integration Tests
- Verify PostgreSQL migrations and service-level transactions.
- Verify Redis helper behavior, caching, rate limiting, OTPs, password reset keys, token blacklist,
  outage fallback, and locks through the shared `learngrid-redis` package and service tests.
- Verify Kafka producers, consumers, retries, dead-letter paths, idempotency, and lag reporting through the shared `learngrid-events` package.
- Verify object storage upload, signed access, metadata, and permission behavior.
- Repo-level integration tests live under `tests/integration/` and use the existing Docker Compose
  PostgreSQL, Redis, Kafka, and MinIO stack. They skip cleanly when the required endpoints are not
  available.

Run:

```bash
python -m pytest tests/integration
```

Configure with `INTEGRATION_DATABASE_URL`, `INTEGRATION_REDIS_URL`,
`INTEGRATION_KAFKA_BOOTSTRAP_SERVERS`, and `INTEGRATION_MINIO_ENDPOINT`.

## TEST-004A Contract Tests
- API contract tests under `tests/contracts/` statically verify OpenAPI wiring for every service.
- Optional live checks use `CONTRACT_SERVICE_URLS` to fetch generated OpenAPI JSON.
- Kafka contract tests validate topic naming, retry/DLQ naming, and representative
  `learngrid-events` envelopes.

Run:

```bash
python -m pytest tests/contracts
```

## TEST-005 Selenium E2E Tests
Required journeys:
- Student login
- Instructor login
- Admin login
- Course creation
- Course publishing
- Student enrollment
- Lesson viewing
- Quiz attempt
- Assignment submission
- Grade viewing
- Role-based access control
- Logout

Suggested structure:

```text
tests/e2e/pages/login_page.py
tests/e2e/pages/dashboard_page.py
tests/e2e/pages/course_page.py
tests/e2e/pages/assessment_page.py
tests/e2e/tests/test_login.py
tests/e2e/tests/test_course_enrollment.py
tests/e2e/tests/test_lesson_completion.py
tests/e2e/tests/test_quiz_submission.py
```

## TEST-006 Load Tests
- Simulate login, dashboard loading, course listing, lesson access, quiz submission, and notifications.
- Use k6 scripts under `tests/load/`.
- Track p95 latency, error rate, throughput, PostgreSQL connections, Redis memory, Kafka lag, CPU, memory, and autoscaling behavior.
- Common API requests target p95 latency below 300 ms under normal load, excluding large file downloads and video streaming.
- CI runs the offline-safe smoke script. Staging runs can set `LOAD_BASE_URL`, role credentials,
  `LOAD_VUS`, and `LOAD_DURATION`.

Run:

```bash
k6 run tests/load/smoke.js
k6 run tests/load/staging.js
```

## TEST-007 Security Tests
- Verify gateway HTTPS redirect, CORS allow/deny behavior, secure headers, rate limits, and request
  size limits.
- Verify production settings require secrets and reject local-only placeholders.
- Verify auth password validation, login/reset rate limiting, protected API denial, and durable
  audit logs for sensitive writes.
- Verify upload MIME type, extension, size, object key validation, signed access, and optional
  malware scanner fail-closed behavior.
- Verify Kubernetes security baseline templates and PostgreSQL backup restore checks in CI.

## TEST-008 Deployment And Observability Tests
- Validate every backend service has a production Dockerfile that runs Gunicorn as a non-root user.
- Validate frontend and gateway images expose `/healthz` and `/gateway/health`.
- Validate Helm charts include Deployments, Services, ConfigMaps, Secret references, HPAs, probes,
  migration Jobs, PDBs, NetworkPolicies, and restricted runtime settings.
- Validate Grafana dashboard JSON and required observability components before cluster deployment.
- CI validates Helm rendering, Kubernetes schemas, image scans, staging smoke tests, and production
  deployment gates.

## TEST-009 Repo Quality Commands
Root-level test utilities are listed in `requirements-test.txt`.

```bash
python -m pytest tests/contracts
python -m pytest tests/integration
python -m pytest tests/e2e
k6 run tests/load/smoke.js
```

CI runs backend `ruff check`, `ruff format --check`, `mypy`, Django checks, migration dry-runs,
and pytest; frontend lint, typecheck, tests, build, and high-severity audit; repo actionlint, shell
syntax, contract, integration, E2E, k6, security, deployment, image, and Helm checks.

## TEST-010 Related Spec And Task
Primary spec: [SPEC-024](specs/024-testing-quality.md).  
Primary task: [T-024](tasks/T-024-testing-quality.md).
