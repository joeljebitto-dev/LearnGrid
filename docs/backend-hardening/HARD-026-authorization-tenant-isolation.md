# HARD-026 Authorization And Tenant Isolation

Related task: [T-026](../tasks/T-026-backend-hardening-api-completion.md)
Related docs: [BACKEND_ARCHITECTURE.md](../BACKEND_ARCHITECTURE.md), [SECURITY.md](../SECURITY.md)
Shared package: [learngrid-authz](../../backend/shared/learngrid-authz)

## HARD-026-AUTHZ-001 Shared Authorization Helper

Non-auth backend services use `learngrid_authz` for remote auth-service checks:

| Interface | Purpose |
| --- | --- |
| `remote_authorization_check(...)` | Calls `POST /api/auth/authorization/check/` and returns `False` on denial, malformed response, timeout, or network failure |
| `require_remote_permission(...)` | Raises DRF `PermissionDenied` when the remote check denies |
| `RemoteAuthorizationPermission` | DRF permission class for endpoints that can declare `required_permission`, `required_scope_type`, and optional scope IDs |

The timeout is controlled by `AUTHORIZATION_CHECK_TIMEOUT_SECONDS`, default `2`.

## HARD-026-AUTHZ-002 Permission Matrix

| Service | Primary permissions | Scope type | Tenant isolation rule |
| --- | --- | --- | --- |
| `user-service` | `profile.view`, `profile.manage`, `institution.manage` | `platform`, `institution` | Institution-scoped profile/organization reads and writes require matching `institution_id`; platform reads are Super Admin only through auth-service policy |
| `course-service` | `course.view`, `course.manage` | `platform`, `institution`, `course` | Course/category/tag writes require request or resource institution scope; course structure writes use the owning course institution |
| `content-service` | `content.view`, `content.manage` | `platform`, `institution` | Asset access and upload workflows require the asset/request institution scope; signed access still validates token and asset state |
| `enrollment-service` | `enrollment.view`, `enrollment.manage` | `platform`, `institution` | Enrollment state, batch/cohort jobs, and access grants are filtered or checked by institution |
| `progress-service` | `progress.view`, `progress.manage` | `platform`, `course` | Course progress reads/writes require the target `course_id`; platform event reads are management-only |
| `assessment-service` | `assessment.view`, `assessment.manage`, `submission.view`, `submission.manage`, `grade.manage` | `platform`, `institution`, `course` | Authoring and grading-source reads check course first, then institution where applicable; student attempts are tied to current profile/enrollment |
| `grading-service` | `grade.view`, `grade.manage` | `platform`, `institution`, `course` | Grade records, results, and certificates are visible to owning students or scoped grade managers only |
| `notification-service` | `notification.view`, `notification.manage` | `platform` | User-facing notifications are filtered by recipient; management operations use platform notification permissions |
| `analytics-service` | `analytics.view`, resource view permissions | `platform`, `institution` | Search/reporting filters are authorized by institution or platform; student/instructor dashboards derive profile from bearer token |

## HARD-026-AUTHZ-003 Test Evidence

- Service tests already monkeypatch each service module’s `remote_authorization_check`; the module
  names remain stable and now delegate to `learngrid_authz`.
- [test_t026_backend_hardening.py](../../tests/contracts/test_t026_backend_hardening.py) verifies
  every non-auth service depends on `learngrid-authz`, declares the timeout setting, and does not
  implement direct `urllib` authorization calls in its permission module.
- Product tests in each service cover authorization denial and cross-scope denial for implemented
  workflows.
