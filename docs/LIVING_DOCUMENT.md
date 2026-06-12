# Living Document

Source: [SRD.pdf](SRD.pdf)

## LD-001 Current State
The repository contains the SRD, documentation set, the completed `T-001` monorepo scaffold,
completed `T-002` token/session security, completed `T-003` RBAC/object authorization, and
completed `T-004` user/profile management, completed `T-005` institution, department, and
batch management, completed `T-006` course catalog metadata, completed `T-007` course
structure/versioning, completed `T-008` content upload/storage/access with MinIO object storage,
completed `T-009` enrollment/access management, completed `T-010`
learning progress tracking, completed `T-011` dashboards/portals, completed `T-012`
assessment authoring, completed `T-013` quiz attempts/exams, completed `T-014`
assignment submissions, completed `T-015` grading/results/audit, completed `T-016`
certificates, completed `T-017` notifications, completed `T-018` search/reporting/analytics,
completed `T-019` API gateway, completed `T-020` Kafka eventing, completed `T-021`
Redis architecture, completed `T-022` security baseline, the repository implementation portion
of `T-023` CI/CD, deployment, and observability, and the repository implementation portion of
`T-024` testing and quality.
The scaffold includes the React `frontend-service`, Django REST Framework baselines for `SVC-001`
through `SVC-010`, local PostgreSQL and Redis Compose configuration, health endpoints, lockfiles,
basic tests, and GitHub Actions CI. Auth-service now includes JWT access and refresh token APIs,
refresh rotation, logout revocation, Redis-backed blacklist checks with durable database fallback,
token invalidation after password changes or account-level revocation, and optional generic OIDC
SSO that links verified provider identities to existing active accounts only. Auth-service also owns
RBAC roles, permissions, scoped role assignments, authorization checks, Redis permission caching,
authorization audit logs, Redis-backed login/reset rate limiting, password reset token state, and
OTP helpers. Non-auth backend services can validate access JWTs and call auth-service
for remote permission checks. User-service now owns institution support models, base user profiles,
student/instructor/admin profile tables, user import job records, and profile create, search, update,
and deactivate APIs that coordinate account lifecycle through auth-service. User-service also exposes
institution, department, and batch management APIs with scoped `institution.manage` authorization,
filtering, pagination, and soft-delete behavior. Course-service now owns course catalog records,
categories, tags, prerequisites, learning outcomes, published catalog cache behavior, lifecycle
workflows, and Kafka-capable structured course events. Course-service also owns ordered modules, lessons,
topics, lesson publishing, structure reordering, and course revision snapshots. Content domain
metadata, MinIO-backed upload and signed access, enrollment/access management, learning
progress tracking, analytics dashboard/report foundations, role-specific frontend portals,
assessment authoring, quiz/exam attempts, assignment submissions, and grading/results/audit
workflows, plus certificate eligibility and auto-issued certificate records, are now implemented
in their owning services. Notification templates, in-app notification records, preferences,
delivery attempts, idempotent notification event ingestion, generalized analytics search/reporting
APIs, and the local Nginx API Gateway are also implemented.
Shared Kafka eventing with Apache Kafka local infrastructure, base/retry/DLQ topics, producer
helpers, consumer helpers, idempotent service handlers, and lag commands is implemented for
`T-020`.
Shared Redis helpers, standardized key naming, course catalog cache keys, course structure locks,
analytics dashboard response caching, and production Redis Sentinel support are implemented for
`T-021`.
Shared production security helpers, hardened gateway headers, production secret validation,
Kubernetes security baseline templates, optional upload malware scanning, and backup restore
verification are implemented for `T-022`. `OD-003` is resolved to on-prem Kubernetes. Backend,
frontend, and gateway production images, Helm deployment charts, liveness/readiness/metrics
endpoints, Grafana-stack observability manifests, GHCR image CI, and deployment workflow gates are
implemented for `T-023`; final task closure still requires a real staging deployment smoke run.
All backend services expose OpenAPI schema/docs endpoints; service schema smoke tests, repo-level
OpenAPI/Kafka contract tests, Compose-backed integration tests, Selenium page-object journey tests,
k6 load scripts, expanded CI quality gates, and staging/performance readiness evidence scripts are
implemented for `T-024`. Final T-024 closure still requires a real staging/on-prem performance and
autoscaling run.

## LD-002 Source Of Truth
- Product and architecture requirements come from [SRD.pdf](SRD.pdf).
- Master requirement index: [SPECIFICATION.md](SPECIFICATION.md).
- Master implementation checklist: [TASKS.md](TASKS.md).
- Intended database schema: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).
- Overall database structure: [DB_STRUCTURE.md](DB_STRUCTURE.md).
- Overall implemented API structure: [API_STRUCTURE.md](API_STRUCTURE.md).
- Implemented database design notes: [db-design/](db-design/README.md).
- Implemented API design notes: [api-design/](api-design/README.md).
- Implemented event design notes: [event-design/](event-design/README.md).
- Security overview: [SECURITY.md](SECURITY.md).
- Implemented security design notes: [security-design/](security-design/README.md).
- Implemented deployment design notes: [deployment-design/](deployment-design/README.md).
- Implemented observability design notes: [observability-design/](observability-design/README.md).

## LD-003 Update Rules
- Add or revise a spec before implementing a new feature.
- Add or revise tasks when implementation scope changes.
- Update [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) before model or migration work.
- Add implemented database design notes under [db-design/](db-design/README.md) after database-backed tasks are complete.
- Add implemented API design notes under [api-design/](api-design/README.md) after API-backed tasks are complete.
- Add implemented event design notes under [event-design/](event-design/README.md) after event-backed tasks are complete.
- Update [DB_STRUCTURE.md](DB_STRUCTURE.md) and [API_STRUCTURE.md](API_STRUCTURE.md) after schema or implemented API changes.
- Move open decisions out of [KNOWN_ISSUES.md](KNOWN_ISSUES.md) only after an explicit decision is recorded.
- Update [CHANGELOG.md](CHANGELOG.md) after meaningful documentation or implementation changes.

## LD-004 Open Decision Register
All SRD open decisions currently tracked in [KNOWN_ISSUES.md](KNOWN_ISSUES.md) are resolved.
Repository-side readiness is complete, but [T-023.06](tasks/T-023-ci-cd-deployment-observability.md)
and [T-024.08](tasks/T-024-testing-quality.md) remain unchecked until real staging deployment,
performance, and autoscaling evidence exists.
