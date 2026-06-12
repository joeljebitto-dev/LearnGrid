# REDIS-021 Redis Architecture

Related task: [T-021 Redis Architecture](../tasks/T-021-redis-architecture.md)  
Related spec: [SPEC-021](../specs/021-redis-architecture.md)

## Design Summary
T-021 adds `backend/shared/learngrid-redis` as the shared Redis helper package. It standardizes
client timeouts, key construction, JSON caches, fixed-window rate limits, and distributed locks.

Redis is used only for cache or temporary/security state. Permanent academic records remain in
PostgreSQL service databases.

## Key Convention
All new keys use:

```text
lg:{REDIS_ENV}:{service}:{workload}:{name}:{suffix}
```

Examples:

| Workload | Example shape |
| --- | --- |
| JWT blacklist | `lg:local:auth-service:blacklist:jwt:<jti>` |
| Permission cache | `lg:local:auth-service:permission-cache:check:<account_uuid>:<permission>:<scope_type>:<scope_uuid>` |
| Login rate limit | `lg:local:auth-service:rate-limit:login:<sha256>` |
| Course catalog cache | `lg:local:course-service:cache:catalog:course-list:<sha256>` |
| Course structure lock | `lg:local:course-service:lock:course-structure:<course_uuid>` |
| Dashboard cache | `lg:local:analytics-service:cache:dashboard:<scope_type>:<scope_uuid>:<portal>:<profile_uuid>` |

Raw emails, IP addresses, query payloads, reset tokens, and OTP subjects are hashed before they
become key suffixes.

## TTLs And Invalidation
| Redis data | Owner | TTL | Invalidation or fallback |
| --- | --- | --- | --- |
| JWT blacklist | `auth-service` | Remaining token lifetime | Durable `token_blacklist` table fallback |
| Permission cache | `auth-service` | `AUTH_PERMISSION_CACHE_TTL_SECONDS`, default `300` | Role and role-permission writes invalidate matching keys; DB fallback |
| Login rate limit | `auth-service` | `AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS`, default `900` | Redis outage fails closed with throttling |
| Password reset token key | `auth-service` | `AUTH_PASSWORD_RESET_TTL_SECONDS`, default `900` | Durable `password_reset_tokens` row tracks pending/used/expired/revoked |
| OTP key | `auth-service` | `AUTH_OTP_TTL_SECONDS`, default `300` | Max attempts from `AUTH_OTP_MAX_ATTEMPTS`, default `5` |
| Course catalog cache | `course-service` | `COURSE_CATALOG_CACHE_TTL_SECONDS`, default `300` | Course/category/tag/structure writes invalidate; DB fallback |
| Course structure lock | `course-service` | `REDIS_LOCK_TTL_SECONDS`, default `30` | Lock contention or Redis outage returns `409` |
| Dashboard response cache | `analytics-service` | `ANALYTICS_DASHBOARD_CACHE_TTL_SECONDS`, default `60` | Dashboard aggregate upserts invalidate affected scope; DB fallback |

## Production Deployment
`OD-003` is resolved by `T-023` to on-prem Kubernetes. The T-023 runtime chart provides the first
in-cluster Redis deployment baseline for production. `T-021.07` remains open for a future
Sentinel/Cluster-specific hardening pass. Local development continues to use the single Redis
container from `docker-compose.yml`.
