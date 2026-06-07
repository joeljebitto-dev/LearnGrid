# SPEC-021 Redis Architecture

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-021](../tasks/T-021-redis-architecture.md)

## Functional Requirements
- SPEC-021-FR-001 Redis shall support API response cache.
- SPEC-021-FR-002 Redis shall support course catalog cache.
- SPEC-021-FR-003 Redis shall support user permission cache.
- SPEC-021-FR-004 Redis shall support JWT blacklist.
- SPEC-021-FR-005 Redis shall support OTP and password reset token cache.
- SPEC-021-FR-006 Redis shall support rate limiting.
- SPEC-021-FR-007 Redis shall support WebSocket channel layer.
- SPEC-021-FR-008 Redis shall support distributed locks.
- SPEC-021-FR-009 Redis shall support temporary assessment attempt state.

## Non-Functional Requirements
- SPEC-021-NFR-001 Redis shall not be the only storage for permanent academic records.
- SPEC-021-NFR-002 Cached data shall use TTLs.
- SPEC-021-NFR-003 Cache shall be invalidated after writes where stale data is harmful.
- SPEC-021-NFR-004 Production Redis shall use Sentinel or Cluster for reliability.
- SPEC-021-NFR-005 Redis workloads may be separated by cache, session, and channel needs.

## Acceptance Criteria
- SPEC-021-AC-001 Sensitive endpoint rate limits are backed by Redis.
- SPEC-021-AC-002 Cache keys have documented TTL and invalidation behavior.
- SPEC-021-AC-003 Redis outage behavior is tested for critical APIs.
- SPEC-021-AC-004 No required permanent academic data exists only in Redis.
