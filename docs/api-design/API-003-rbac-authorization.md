# API-003 RBAC Authorization

Related task: [T-003 RBAC And Object Authorization](../tasks/T-003-rbac-object-authorization.md)  
Related spec: [SPEC-003 RBAC Object Authorization](../specs/003-rbac-object-authorization.md)  
Related database design: [DBD-003](../db-design/DBD-003-rbac-authorization.md)

## Design Summary
T-003 implemented centralized RBAC APIs in `auth-service` and JWT-aware remote authorization helpers for all non-auth backend services. Permission checks are deny-by-default when authentication is invalid or auth-service cannot confirm access.

## Endpoints
| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/auth/rbac/roles/` | `rbac.manage` | List seeded roles |
| `GET` | `/api/auth/rbac/permissions/` | `rbac.manage` | List permission catalog |
| `POST` | `/api/auth/rbac/role-assignments/` | `rbac.manage` | Assign a role to an account and scope |
| `DELETE` | `/api/auth/rbac/role-assignments/<uuid>/` | `rbac.manage` | Revoke a role assignment |
| `POST` | `/api/auth/authorization/check/` | Access token | Check whether the current account has a permission in a scope |

## Role Assignment Request
```json
{
  "account_id": "<uuid>",
  "role_code": "student",
  "scope_type": "course",
  "scope_id": "<uuid>"
}
```

Platform role assignments require the actor to have the `super_admin` role.

## Authorization Check Request And Response
```json
{
  "permission": "course.view",
  "scope_type": "course",
  "scope_id": "<uuid>"
}
```

```json
{ "allowed": true }
```

## Auth And Failure Behavior
- Non-auth services validate access JWTs locally using shared issuer/signing settings.
- Non-auth services call `/api/auth/authorization/check/` for protected object access.
- If auth-service is unreachable, returns unauthorized, or returns `allowed: false`, the caller denies access.
- Permission results are cached in Redis and invalidated after role changes.

## Verification
T-003 tests cover seeded roles and permissions, role-permission mappings, platform/institution/course/assessment scopes, Super Admin behavior, scoped denial, audit logs, Redis cache use/invalidation, Redis fallback, authorization endpoint behavior, non-auth JWT validation, and remote permission denial paths.
