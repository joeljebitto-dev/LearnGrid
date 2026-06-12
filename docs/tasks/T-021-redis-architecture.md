# T-021 Redis Architecture

Related spec: [SPEC-021](../specs/021-redis-architecture.md)

- [x] T-021.01 Define Redis key naming conventions.
- [x] T-021.02 Implement API response cache behavior where useful.
- [x] T-021.03 Implement course catalog cache.
- [x] T-021.04 Implement user permission cache.
- [x] T-021.05 Implement OTP, password reset, token blacklist, and rate limit keys with TTLs.
- [x] T-021.06 Implement distributed lock helper where needed.
- [x] T-021.07 Configure production Redis Sentinel or Cluster after deployment model is selected.
- [x] T-021.08 Add tests for TTLs, invalidation, outage handling, and cache misses.

## Verification Notes
- Added shared `learngrid-redis` helpers for key naming, JSON cache, rate limits, and locks.
- Implemented Redis-backed auth rate limits, password reset TTL keys, OTP helpers, blacklist key
  conventions, permission cache key conventions, hashed course catalog cache keys, course
  structure locks, and analytics dashboard response cache.
- `OD-003` is resolved by `T-023` to on-prem Kubernetes. Production Redis HA is implemented as
  Redis Sentinel with primary/replica pods, Sentinel service on `26379`, and app-side Sentinel
  client selection through `REDIS_SENTINEL_URLS`.
- Verification passed in Docker with Poetry: shared package Ruff/pytest; auth-service,
  course-service, and analytics-service Ruff, Django system check, migration dry-run, and pytest.
