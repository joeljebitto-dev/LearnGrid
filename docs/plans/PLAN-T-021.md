# T-021 Redis Architecture Plan

## Summary
Implement Redis as a standardized shared backend capability while preserving existing service behavior. Add missing Redis-backed rate limiting, OTP/password reset keys, distributed locks, and focused tests. Keep production Sentinel/Cluster unresolved because `OD-003 Deployment Model` is still open.

## Key Changes
- Add `backend/shared/learngrid-redis` with helpers for Redis clients, key building, JSON caches, fixed-window rate limits, and safe distributed locks.
- Standard key format: `lg:{REDIS_ENV}:{service}:{workload}:{name}:{suffix}`. Use UUIDs or SHA-256 digests for user identifiers, request params, and secrets; never place raw email, IP, token, or query JSON in keys.
- Retrofit `auth-service` Redis usage:
  - Token blacklist keys use remaining-token TTL and durable DB fallback.
  - Permission cache uses standardized keys, `AUTH_PERMISSION_CACHE_TTL_SECONDS=300`, and existing invalidation after RBAC writes.
  - Add Redis-backed login/password-reset rate limits that fail closed when Redis is unavailable.
  - Add `PasswordResetToken` model/migration matching `DB-AUTH-005`, plus minimal reset request/confirm APIs.
  - Add OTP helper functions with TTL, max-attempt tracking, and no permanent academic/user data stored only in Redis.
- Retrofit `course-service`:
  - Course catalog cache uses standardized hashed keys and `COURSE_CATALOG_CACHE_TTL_SECONDS=300`.
  - Keep DB fallback on cache miss/outage.
  - Wrap course/module/lesson/topic reorder writes with Redis distributed locks; lock contention returns a conflict-style API error.
- Add API response cache where useful in `analytics-service`:
  - Cache dashboard payload responses with `ANALYTICS_DASHBOARD_CACHE_TTL_SECONDS=60`.
  - Invalidate affected dashboard cache keys after dashboard aggregate upserts.
  - Fall back to DB reads when Redis cache is unavailable.
- Add Redis design documentation under `docs/redis-design/`, update development/API/backend/testing docs, changelog, living document, `.env.example`, and task checklist.
- Mark `T-021.01` through `T-021.06` and `T-021.08` complete after verification. Leave `T-021.07` unchecked with a note that Sentinel/Cluster selection waits for `OD-003`.

## Public Interfaces
- New auth endpoints:
  - `POST /api/auth/password-reset/request/` with `{ "email": "user@example.com" }`, always returns `{ "status": "accepted" }`.
  - `POST /api/auth/password-reset/confirm/` with `{ "token": "...", "new_password": "..." }`, returns `{ "status": "reset" }`.
- New settings:
  - `REDIS_ENV=local`, Redis socket/connect timeout settings, `REDIS_LOCK_TTL_SECONDS=30`.
  - `AUTH_LOGIN_RATE_LIMIT_COUNT=5`, `AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS=900`.
  - `AUTH_PASSWORD_RESET_RATE_LIMIT_COUNT=3`, `AUTH_PASSWORD_RESET_TTL_SECONDS=900`.
  - `AUTH_OTP_TTL_SECONDS=300`, `AUTH_OTP_MAX_ATTEMPTS=5`.
  - `ANALYTICS_DASHBOARD_CACHE_TTL_SECONDS=60`.
- Password reset raw tokens are not exposed by default; tests may enable a debug/test-only setting for response visibility.

## Test Plan
- Shared package tests: key normalization/digests, JSON cache TTL/miss/outage behavior, fixed-window rate limit TTL/overflow, safe lock acquire/release/ownership.
- Auth tests: blacklist TTL and DB fallback, permission cache TTL/invalidation/fallback, login/reset rate limits, password reset success/expired/reused/outage cases, OTP issue/verify/max-attempt behavior.
- Course tests: catalog cache miss/hit/TTL/invalidation, hashed cache keys, Redis outage fallback, reorder lock success/contention/outage.
- Analytics tests: dashboard response cache hit/miss/invalidation and Redis outage fallback.
- Verification commands: `poetry lock`, `poetry run ruff check .`, `poetry run python manage.py check`, `poetry run python manage.py makemigrations --check --dry-run`, and `poetry run pytest` for changed services plus shared-package Ruff/pytest.

## Assumptions
- Do not resolve `OD-003`; production Sentinel/Cluster config is documented as deferred.
- Redis is never the only storage for permanent academic records.
- Security-sensitive Redis dependencies such as rate limiting, OTP, password reset, and locks fail closed on Redis outage; caches fall back to source-of-truth reads.
