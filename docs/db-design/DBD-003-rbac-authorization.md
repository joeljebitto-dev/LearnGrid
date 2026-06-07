# DBD-003 RBAC Authorization

Related task: [T-003 RBAC And Object Authorization](../tasks/T-003-rbac-object-authorization.md)  
Related spec: [SPEC-003 RBAC Object Authorization](../specs/003-rbac-object-authorization.md)  
Canonical schema: [auth_db](../DATABASE_SCHEMA.md#auth_db)

## Design Summary
T-003 extended `auth_db` with RBAC tables, role assignment scopes, authorization audit logging, and Redis-backed permission caching. `auth-service` is the source of truth for authorization; other services validate JWTs locally and ask `auth-service` for permission decisions.

## Implemented Tables
| Table ID | Table | Purpose |
| --- | --- | --- |
| `DB-AUTH-007` | `roles` | Seeded system roles and role scope type |
| `DB-AUTH-008` | `permissions` | Permission catalog such as `profile.view` and `rbac.manage` |
| `DB-AUTH-009` | `role_permissions` | Role-to-permission mapping |
| `DB-AUTH-010` | `role_assignments` | Account role grants at platform, institution, course, or assessment scope |
| `DB-AUTH-011` | `authorization_audit_logs` | Role assignment and role-permission change audit events |

## Seeded Authorization Model
- Roles: `super_admin`, `institution_admin`, `instructor`, `teaching_assistant`, `student`, and `parent_guardian`.
- Scope types: `platform`, `institution`, `course`, and `assessment` for assignments.
- `super_admin` grants platform-wide access to all seeded permissions.
- Scoped assignments grant permissions only for exact matching scopes, with platform roles applying globally.

## Indexes And Constraints
- Role and permission codes are unique.
- `role_permissions` prevents duplicate role-permission pairs.
- `role_assignments` prevents duplicate active platform or scoped assignments.
- Authorization audit logs keep actor, target account, role, permission, scope, request metadata, and timestamp.

## Redis Permission Cache
Effective permission checks are cached in Redis with `AUTH_PERMISSION_CACHE_TTL_SECONDS`, default `300`. Cache entries are invalidated after role assignment or role-permission changes. When Redis is unavailable, permission checks fall back to database queries.

## Verification
T-003 tests cover seeded roles and permissions, role-permission mappings, exact scope enforcement, Super Admin behavior, audit logs, cache use, cache invalidation, Redis fallback, authorization endpoint behavior, and non-auth service JWT/remote permission helpers.
