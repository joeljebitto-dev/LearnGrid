# T-026 Backend Hardening And API Completion Plan

## Summary
Implement `T-026` as repository-side backend hardening across all Django services. This is not a new product feature task; it will tighten existing APIs, authorization, tenant isolation, eventing, content safety, analytics/reporting, notifications, certificates, migration practices, retention/audit documentation, and backend test coverage.

## Key Changes
- Add a backend hardening evidence set under `docs/backend-hardening/`:
  - API completeness matrix for every service against `docs/API_STRUCTURE.md`.
  - Authorization and tenant-isolation matrix by endpoint, permission, scope type, and owning service.
  - Kafka producer/consumer coverage matrix with retry, DLQ, replay, and idempotency notes.
  - Background workflow runbook for imports, notification processing, analytics reports, Kafka consumers, maintenance jobs, and operational commands.
  - Migration/backfill/rollback runbook and retention/audit/compliance record policy.

- Centralize cross-service authorization behavior:
  - Add a shared internal helper package, `backend/shared/learngrid-authz`, for remote auth-service checks, scope resolution, deny-by-default behavior, timeout handling, and test fakes.
  - Replace duplicated `remote_authorization_check` implementations in non-auth services with this helper.
  - Preserve existing public API paths and backend authorization as authoritative.

- Standardize API behavior without breaking bounded nested reads:
  - Top-level collection/search endpoints use DRF-style pagination: `count`, `next`, `previous`, `results`.
  - Bounded nested reads such as course structure children may remain arrays, but must be documented as bounded.
  - Standardize `q`, `sort`, `page`, `page_size`, status filters, validation errors, empty responses, and max page size across services.

- Harden high-risk workflows:
  - Analytics: large-result pagination, filtered search/report tests, no cross-service DB joins, stable empty responses.
  - Notifications: template/preference enforcement, event ingestion idempotency, retry-safe dispatch records, read/unread behavior.
  - Certificates: eligibility idempotency, revocation visibility, asset validation, student/manager result visibility.
  - Content: object-key safety, MIME/extension/size checks, optional malware scan fail-closed behavior, upload failure cleanup.
  - Kafka: consumer duplicate/retry/DLQ/replay tests and service-specific handler coverage for analytics, notifications, and progress.

- Expand backend tests and contract checks:
  - Add repo-level T-026 contract tests for endpoint inventory, permission inventory, pagination conventions, event topic coverage, and migration reversibility rules.
  - Add or extend service tests for authorization denial, cross-institution access denial, empty responses, large lists, event idempotency, notification preferences, certificate revocation, and content validation.
  - Update `docs/tasks/T-026-backend-hardening-api-completion.md` only after verification passes.

## Public Interfaces
- No new product API endpoints are added.
- Existing endpoint paths remain stable.
- Top-level list/search endpoints are standardized to paginated responses where not already paginated.
- New internal Python interfaces:
  - `learngrid_authz.remote_authorization_check(...)`
  - `learngrid_authz.require_remote_permission(...)`
  - `learngrid_authz.RemoteAuthorizationPermission`
- New optional setting:
  - `AUTHORIZATION_CHECK_TIMEOUT_SECONDS`, default `2`.

## Test Plan
- Per changed backend service:
  - `poetry run ruff check .`
  - `poetry run ruff format --check .`
  - `poetry run mypy .`
  - `poetry run python manage.py check`
  - `poetry run python manage.py makemigrations --check --dry-run`
  - `poetry run pytest`

- Shared packages:
  - `learngrid-authz`, `learngrid-events`, `learngrid-security`, and `learngrid-redis`: `poetry run ruff check .` and `poetry run pytest`.

- Repo-level:
  - `python -m pytest tests/contracts`
  - `python -m pytest tests/integration`
  - `python -m pytest tests/security`
  - `k6 run tests/load/smoke.js`
  - `git diff --check`

## Assumptions
- Implement on top of the current repository state and preserve unrelated worktree changes.
- T-026 does not replace completed feature tasks; any discovered product gap is linked back to its owning task or documented for later follow-up.
- `T-023.06` and `T-024.08` remain unchecked because they require real staging CI/CD and performance evidence.
- No frontend changes are required except if API response standardization exposes a compatibility issue.
