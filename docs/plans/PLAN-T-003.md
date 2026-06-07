# T-003 RBAC And Object Authorization Plan

## Summary
Implement T-003 across all backend services. `auth-service` will own the RBAC data model, permission catalog, role assignment APIs, authorization checks, audit logs, and Redis permission cache. Other backend services will get JWT-aware authentication helpers and remote authorization permission classes that call `auth-service`.

## Key Changes
- Extend `auth-service` with schema-backed RBAC:
  - Add `Role`, `Permission`, `RolePermission`, `RoleAssignment`, and `AuthorizationAuditLog`.
  - Add a migration that creates the RBAC tables and seeds system roles, permissions, and role-permission mappings.
  - Use generic UUID scopes: `platform`, `institution`, `course`, and `assessment`.
  - Keep role scope types aligned with docs: `platform`, `institution`, `course`; allow role assignments at `assessment` scope.

- Add authorization services and cache:
  - Implement `has_permission(account, permission, scope_type, scope_id)` and object-scope helpers.
  - Super Admin grants platform-wide access.
  - Scoped roles grant only exact matching scope access, plus platform roles applying globally.
  - Cache effective permission checks in Redis with `AUTH_PERMISSION_CACHE_TTL_SECONDS`, default `300`.
  - Invalidate permission cache after role assignment or role-permission changes.
  - Fall back to database permission checks when Redis is unavailable.

- Add auth-service RBAC APIs:
  - `GET /api/auth/rbac/roles/`
  - `GET /api/auth/rbac/permissions/`
  - `POST /api/auth/rbac/role-assignments/`
  - `DELETE /api/auth/rbac/role-assignments/<uuid>/`
  - `POST /api/auth/authorization/check/`
  - Management endpoints require `rbac.manage`; platform assignments require Super Admin.

- Wire all backend services for authorization:
  - Add shared-style JWT authentication and remote permission helpers to each non-auth service.
  - Add `AUTH_SERVICE_BASE_URL`, `AUTH_JWT_SIGNING_KEY`, `AUTH_JWT_ISSUER`, and `AUTH_JWT_ALGORITHM` settings.
  - Add `pyjwt` to non-auth service Poetry dependencies.
  - Permission helpers deny by default if auth-service is unreachable or returns unauthorized.
  - Existing `/health/` endpoints remain public.

- Update documentation:
  - Update `DATABASE_SCHEMA.md` for the new authorization audit table.
  - Document RBAC APIs, permission cache behavior, JWT signing key sharing, and service authorization usage.
  - Mark `T-003.01` through `T-003.08` complete only after verification passes.

## Seeded Roles And Permissions
- Roles:
  - `super_admin`
  - `institution_admin`
  - `instructor`
  - `teaching_assistant`
  - `student`
  - `parent_guardian`

- Initial permission catalog:
  - `rbac.manage`
  - `institution.manage`
  - `profile.view`, `profile.manage`
  - `course.view`, `course.manage`
  - `content.view`, `content.manage`
  - `enrollment.view`, `enrollment.manage`
  - `progress.view`, `progress.manage`
  - `assessment.view`, `assessment.manage`
  - `submission.view`, `submission.manage`
  - `grade.view`, `grade.manage`
  - `notification.view`, `notification.manage`
  - `analytics.view`

## Test Plan
- Auth-service tests:
  - seeded roles and permissions exist;
  - role-permission mappings are correct;
  - platform, institution, course, and assessment scopes are enforced;
  - Super Admin can perform platform-wide checks;
  - scoped users are denied outside their scope;
  - role assignment creation/revocation writes audit logs;
  - Redis permission cache is used and invalidated;
  - Redis failure falls back to database checks;
  - authorization check endpoint denies without leaking object existence.

- Non-auth service tests:
  - JWT authentication accepts valid access tokens and rejects malformed/expired tokens;
  - remote permission class allows authorized responses;
  - remote permission class denies unauthorized responses;
  - auth-service network failure denies access.

- Verification commands:
  - `poetry lock` where dependencies change;
  - `poetry run ruff check .`;
  - `poetry run python manage.py check`;
  - `poetry run python manage.py makemigrations --check --dry-run`;
  - `poetry run pytest` for every backend service.

## Assumptions
- This implements the selected “all services now” scope.
- `auth-service` remains the RBAC source of truth; other services do not read `auth_db` directly.
- OAuth2/SSO remains unresolved under `OD-004`.
- Domain-specific ownership checks, such as course-to-institution hierarchy, will be added when those domain models exist; T-003 supports exact scoped UUID authorization now.
