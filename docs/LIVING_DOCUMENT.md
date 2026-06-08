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
assessment authoring, and completed `T-013` quiz attempts/exams.
The scaffold includes the React `frontend-service`, Django REST Framework baselines for `SVC-001`
through `SVC-010`, local PostgreSQL and Redis Compose configuration, health endpoints, lockfiles,
basic tests, and GitHub Actions CI. Auth-service now includes JWT access and refresh token APIs,
refresh rotation, logout revocation, Redis-backed blacklist checks with durable database fallback,
and token invalidation after password changes or account-level revocation. Auth-service also owns
RBAC roles, permissions, scoped role assignments, authorization checks, Redis permission caching,
and authorization audit logs. Non-auth backend services can validate access JWTs and call auth-service
for remote permission checks. User-service now owns institution support models, base user profiles,
student/instructor/admin profile tables, user import job records, and profile create, search, update,
and deactivate APIs that coordinate account lifecycle through auth-service. User-service also exposes
institution, department, and batch management APIs with scoped `institution.manage` authorization,
filtering, pagination, and soft-delete behavior. Course-service now owns course catalog records,
categories, tags, prerequisites, learning outcomes, published catalog cache behavior, lifecycle
workflows, and local structured course events. Course-service also owns ordered modules, lessons,
topics, lesson publishing, structure reordering, and course revision snapshots. Content domain
metadata, MinIO-backed upload and signed access, enrollment/access management, learning
progress tracking, analytics dashboard/report foundations, role-specific frontend portals,
assessment authoring, and quiz/exam attempts are now implemented in their owning services.
Assignment submissions, Kubernetes manifests, and remaining
non-auth feature APIs remain for later tasks.

## LD-002 Source Of Truth
- Product and architecture requirements come from [SRD.pdf](SRD.pdf).
- Master requirement index: [SPECIFICATION.md](SPECIFICATION.md).
- Master implementation checklist: [TASKS.md](TASKS.md).
- Intended database schema: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).
- Overall database structure: [DB_STRUCTURE.md](DB_STRUCTURE.md).
- Overall implemented API structure: [API_STRUCTURE.md](API_STRUCTURE.md).
- Implemented database design notes: [db-design/](db-design/README.md).
- Implemented API design notes: [api-design/](api-design/README.md).

## LD-003 Update Rules
- Add or revise a spec before implementing a new feature.
- Add or revise tasks when implementation scope changes.
- Update [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) before model or migration work.
- Add implemented database design notes under [db-design/](db-design/README.md) after database-backed tasks are complete.
- Add implemented API design notes under [api-design/](api-design/README.md) after API-backed tasks are complete.
- Update [DB_STRUCTURE.md](DB_STRUCTURE.md) and [API_STRUCTURE.md](API_STRUCTURE.md) after schema or implemented API changes.
- Move open decisions out of [KNOWN_ISSUES.md](KNOWN_ISSUES.md) only after an explicit decision is recorded.
- Update [CHANGELOG.md](CHANGELOG.md) after meaningful documentation or implementation changes.

## LD-004 Open Decision Register
The following decisions remain open:
- [OD-001 API Gateway Selection](KNOWN_ISSUES.md#od-001-api-gateway-selection)
- [OD-003 Deployment Model](KNOWN_ISSUES.md#od-003-deployment-model)
- [OD-004 Authentication Model](KNOWN_ISSUES.md#od-004-authentication-model)
- [OD-005 Analytics Storage](KNOWN_ISSUES.md#od-005-analytics-storage)
- [OD-006 Video Delivery Strategy](KNOWN_ISSUES.md#od-006-video-delivery-strategy)
