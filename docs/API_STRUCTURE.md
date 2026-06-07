# LearnGrid LMS API Structure

Source of truth: [api-design/](api-design/README.md)
Related implementation docs: [DEVELOPMENT.md](DEVELOPMENT.md), [TASKS.md](TASKS.md)
Related implemented designs: [API-001](api-design/API-001-service-health-and-dev-stack.md), [API-002](api-design/API-002-token-session-security.md), [API-003](api-design/API-003-rbac-authorization.md), [API-004](api-design/API-004-user-profile-management.md), [API-005](api-design/API-005-institution-batch-department-management.md), [API-006](api-design/API-006-course-catalog-metadata.md)

This file is the overall API structure reference for implemented LearnGrid LMS APIs. Future task APIs are intentionally not expanded here until implementation provides stable request and response contracts.

## API-000 Common Rules
- Backend APIs are JSON REST endpoints.
- Protected endpoints require a bearer access token unless marked public.
- Non-auth services validate JWTs locally and call `auth-service` for authorization decisions.
- Paginated list responses use DRF shape: `count`, `next`, `previous`, and `results`.
- UUID path parameters are formatted as `<uuid>`.
- Authorization denial or unreachable remote authorization denies access by default.

## API-001 Development Stack And Health

### API-001-001 Backend Health
Purpose: Verify service process identity and readiness for local checks.
Implemented by: all ten backend services.

| Item | Value |
| --- | --- |
| Method | `GET` |
| Path | `/health/` |
| Auth | Public |
| Path parameters | None |
| Query parameters | None |
| Request body | None |
| Response fields | `service` string; `status` string, currently `ok` |
| Status behavior | `200` when the service is running |

Backend service ports:

| Service | Local URL |
| --- | --- |
| `auth-service` | `http://127.0.0.1:8001/health/` |
| `user-service` | `http://127.0.0.1:8002/health/` |
| `course-service` | `http://127.0.0.1:8003/health/` |
| `content-service` | `http://127.0.0.1:8004/health/` |
| `enrollment-service` | `http://127.0.0.1:8005/health/` |
| `progress-service` | `http://127.0.0.1:8006/health/` |
| `assessment-service` | `http://127.0.0.1:8007/health/` |
| `grading-service` | `http://127.0.0.1:8008/health/` |
| `notification-service` | `http://127.0.0.1:8009/health/` |
| `analytics-service` | `http://127.0.0.1:8010/health/` |

### API-001-002 Local Developer Commands
Purpose: Run the implemented local stack and supporting infrastructure.

| Command | Parameters | Purpose |
| --- | --- | --- |
| `pnpm dev` | Optional env `POETRY_BIN`; no CLI parameters | Start PostgreSQL, Redis, ten backend services, and frontend with installs/migrations |
| `pnpm dev:fast` | Optional env `POETRY_BIN`; no CLI parameters | Start the stack while skipping installs and migrations |
| `pnpm dev:infra` | None | Start PostgreSQL and Redis |
| `pnpm dev:infra:down` | None | Stop Docker Compose infrastructure |

## API-002 Auth Token And Session APIs

### API-002-001 Issue Token Pair
Purpose: Authenticate an account and issue access and refresh JWTs.

| Item | Value |
| --- | --- |
| Service | `auth-service` |
| Method | `POST` |
| Path | `/api/auth/token/issue/` |
| Auth | Public |
| Path parameters | None |
| Query parameters | None |

Request body parameters:

| Parameter | Required | Type | Purpose |
| --- | --- | --- | --- |
| `email` | Yes | string/email | Login identifier |
| `password` | Yes | string | Account password |
| `device_label` | No | string | Human-readable client/device label stored with refresh token |

Response fields:

| Field | Type | Purpose |
| --- | --- | --- |
| `access` | string/JWT | Short-lived access token |
| `refresh` | string/JWT | Refresh token used for rotation |
| `access_expires_at` | ISO datetime | Access token expiry |
| `refresh_expires_at` | ISO datetime | Refresh token expiry |

Status behavior: `200` on success; authentication failure rejects invalid credentials or inactive accounts.

### API-002-002 Refresh Token Pair
Purpose: Rotate a refresh token and issue a new access/refresh pair.

| Item | Value |
| --- | --- |
| Service | `auth-service` |
| Method | `POST` |
| Path | `/api/auth/token/refresh/` |
| Auth | Public with refresh token payload |
| Path parameters | None |
| Query parameters | None |

Request body parameters:

| Parameter | Required | Type | Purpose |
| --- | --- | --- | --- |
| `refresh` | Yes | string/JWT | Active refresh token to rotate |

Response fields: same as [API-002-001](#api-002-001-issue-token-pair).
Status behavior: `200` on success; malformed, expired, revoked, reused, or password-stale refresh tokens are rejected.

### API-002-003 Logout
Purpose: Revoke a refresh token and optionally blacklist the current access token.

| Item | Value |
| --- | --- |
| Service | `auth-service` |
| Method | `POST` |
| Path | `/api/auth/logout/` |
| Auth | Public with token payload |
| Path parameters | None |
| Query parameters | None |

Request body parameters:

| Parameter | Required | Type | Purpose |
| --- | --- | --- | --- |
| `refresh` | Yes | string/JWT | Refresh token to revoke |
| `access` | No | string/JWT | Access token to blacklist immediately |

Response fields:

| Field | Type | Purpose |
| --- | --- | --- |
| `status` | string | Revocation result, currently `revoked` |

Status behavior: `200` on successful revocation; invalid token payloads are rejected.

### API-002-004 Session
Purpose: Return identity for the current access token.

| Item | Value |
| --- | --- |
| Service | `auth-service` |
| Method | `GET` |
| Path | `/api/auth/session/` |
| Auth | Bearer access token |
| Path parameters | None |
| Query parameters | None |
| Request body | None |

Response fields:

| Field | Type | Purpose |
| --- | --- | --- |
| `account_id` | UUID | Auth account identifier |
| `email` | string/email | Account email |
| `status` | string | Account lifecycle status |

Status behavior: `200` on success; malformed, expired, revoked, wrong-type, inactive, or password-stale access tokens are rejected.

## API-003 RBAC And Authorization APIs

### API-003-001 List Roles
Purpose: List seeded RBAC roles.

| Item | Value |
| --- | --- |
| Service | `auth-service` |
| Method | `GET` |
| Path | `/api/auth/rbac/roles/` |
| Auth | Bearer access token with `rbac.manage` |
| Path parameters | None |
| Query parameters | None |
| Request body | None |
| Response fields | Array of role objects: `id`, `code`, `name`, `scope_type`, `is_system` |
| Status behavior | `200` on success; authorization failure denies access |

### API-003-002 List Permissions
Purpose: List the permission catalog.

| Item | Value |
| --- | --- |
| Service | `auth-service` |
| Method | `GET` |
| Path | `/api/auth/rbac/permissions/` |
| Auth | Bearer access token with `rbac.manage` |
| Path parameters | None |
| Query parameters | None |
| Request body | None |
| Response fields | Array of permission objects: `id`, `code`, `resource`, `action`, `description` |
| Status behavior | `200` on success; authorization failure denies access |

### API-003-003 Create Role Assignment
Purpose: Assign a role to an account at platform, institution, course, or assessment scope.

| Item | Value |
| --- | --- |
| Service | `auth-service` |
| Method | `POST` |
| Path | `/api/auth/rbac/role-assignments/` |
| Auth | Bearer access token with `rbac.manage`; platform assignment requires Super Admin |
| Path parameters | None |
| Query parameters | None |

Request body parameters:

| Parameter | Required | Type | Purpose |
| --- | --- | --- | --- |
| `account_id` | Yes | UUID | Target account receiving the role |
| `role_code` | Yes | string | Role code, such as `student` or `institution_admin` |
| `scope_type` | Yes | string enum | Scope: `platform`, `institution`, `course`, or `assessment` |
| `scope_id` | Required for non-platform | UUID/null | Scoped resource identifier |

Response fields:

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | UUID | Role assignment identifier |
| `account_id` | UUID | Target account |
| `role_code` | string | Assigned role |
| `scope_type` | string | Assignment scope type |
| `scope_id` | UUID/null | Scope identifier |
| `assigned_by_account_id` | UUID/null | Actor account |
| `assigned_at` | ISO datetime | Assignment time |
| `revoked_at` | ISO datetime/null | Revocation time |

Status behavior: `201` on success; invalid scope, missing scope ID, or insufficient permission is rejected.

### API-003-004 Revoke Role Assignment
Purpose: Revoke an active role assignment.

| Item | Value |
| --- | --- |
| Service | `auth-service` |
| Method | `DELETE` |
| Path | `/api/auth/rbac/role-assignments/<uuid>/` |
| Auth | Bearer access token with `rbac.manage` |

Path parameters:

| Parameter | Type | Purpose |
| --- | --- | --- |
| `uuid` | UUID | Role assignment ID |

Response fields:

| Field | Type | Purpose |
| --- | --- | --- |
| `status` | string | Revocation result, currently `revoked` |

Status behavior: `200` on success; missing assignment or insufficient permission is rejected.

### API-003-005 Authorization Check
Purpose: Check whether the current account has a permission in a scope.

| Item | Value |
| --- | --- |
| Service | `auth-service` |
| Method | `POST` |
| Path | `/api/auth/authorization/check/` |
| Auth | Bearer access token |
| Path parameters | None |
| Query parameters | None |

Request body parameters:

| Parameter | Required | Type | Purpose |
| --- | --- | --- | --- |
| `permission` | Yes | string | Permission code, such as `profile.view` |
| `scope_type` | No | string enum | Defaults to `platform`; supports `platform`, `institution`, `course`, `assessment` |
| `scope_id` | Required for non-platform | UUID/null | Scoped resource identifier |

Response fields:

| Field | Type | Purpose |
| --- | --- | --- |
| `allowed` | boolean | Whether the permission check passed |

Status behavior: `200` with `allowed`; invalid tokens or malformed scope checks are rejected.

## API-004 Account Lifecycle APIs

### API-004-001 Create Account
Purpose: Create an auth account, password credential, and optional initial RBAC role assignment.

| Item | Value |
| --- | --- |
| Service | `auth-service` |
| Method | `POST` |
| Path | `/api/auth/accounts/` |
| Auth | Bearer access token with `profile.manage`; platform scope requires Super Admin |
| Path parameters | None |
| Query parameters | None |

Request body parameters:

| Parameter | Required | Type | Purpose |
| --- | --- | --- | --- |
| `email` | Yes | string/email | Account email |
| `phone` | No | string/null | Optional account phone |
| `temporary_password` | Yes | string | Initial password; stored as hash only |
| `role_code` | No | string | Optional initial role assignment |
| `scope_type` | No | string enum | Assignment/account operation scope; defaults to `platform` |
| `scope_id` | Required for non-platform | UUID/null | Scoped institution/course/assessment identifier |

Response fields:

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | UUID | Account ID |
| `email` | string/email | Account email |
| `phone` | string/null | Account phone |
| `status` | string | Account status |
| `must_change_password` | boolean | Whether the account must change password |
| `created_at` | ISO datetime | Creation time |
| `updated_at` | ISO datetime | Update time |
| `deleted_at` | ISO datetime/null | Soft-delete/deactivation time |

Status behavior: `201` on success; invalid role, invalid scope, duplicate email/phone, or insufficient authorization is rejected.

### API-004-002 Update Account
Purpose: Update allowed account identity/status fields.

| Item | Value |
| --- | --- |
| Service | `auth-service` |
| Method | `PATCH` |
| Path | `/api/auth/accounts/<uuid>/` |
| Auth | Bearer access token with `profile.manage`; platform scope requires Super Admin |

Path parameters:

| Parameter | Type | Purpose |
| --- | --- | --- |
| `uuid` | UUID | Account ID |

Request body parameters:

| Parameter | Required | Type | Purpose |
| --- | --- | --- | --- |
| `email` | No | string/email | New account email |
| `phone` | No | string/null | New or cleared phone |
| `status` | No | string enum | Account status |
| `scope_type` | No | string enum | Authorization scope; defaults to `platform` |
| `scope_id` | Required for non-platform | UUID/null | Scoped resource identifier |

Response fields: same as [API-004-001](#api-004-001-create-account).
Status behavior: `200` on success; not found, duplicate values, invalid scope, or insufficient authorization is rejected.

### API-004-003 Deactivate Account
Purpose: Deactivate an auth account and revoke active tokens.

| Item | Value |
| --- | --- |
| Service | `auth-service` |
| Method | `POST` |
| Path | `/api/auth/accounts/<uuid>/deactivate/` |
| Auth | Bearer access token with `profile.manage`; platform scope requires Super Admin |

Path parameters:

| Parameter | Type | Purpose |
| --- | --- | --- |
| `uuid` | UUID | Account ID |

Request body parameters:

| Parameter | Required | Type | Purpose |
| --- | --- | --- | --- |
| `scope_type` | No | string enum | Authorization scope; defaults to `platform` |
| `scope_id` | Required for non-platform | UUID/null | Scoped resource identifier |

Response fields: same as [API-004-001](#api-004-001-create-account).
Status behavior: `200` on success; active refresh tokens are revoked and access tokens are invalidated by password-change timestamp.

## API-005 User Profile APIs

### API-005-001 Create Profile
Purpose: Create an auth account through auth-service and create base plus role-specific profile data in user-service.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `POST` |
| Path | `/api/users/profiles/` |
| Auth | Bearer access token with `profile.manage` at institution or platform scope |
| Path parameters | None |
| Query parameters | None |

Request body parameters:

| Parameter | Required | Type | Purpose |
| --- | --- | --- | --- |
| `email` | Yes | string/email | Auth account email |
| `phone` | No | string/null | Auth account phone |
| `temporary_password` | Yes | string | Initial password sent to auth-service |
| `profile_type` | Yes | string enum | `student`, `instructor`, or `admin` |
| `role_code` | No | string | Optional role override for auth-service assignment |
| `institution_id` | No | UUID/null | Profile institution; absent means platform scope |
| `first_name` | Yes | string | Profile first name |
| `last_name` | Yes | string | Profile last name |
| `display_name` | No | string/null | UI display name |
| `avatar_url` | No | string/null | Avatar URL |
| `metadata` | No | object | Flexible profile metadata |
| `student` | Required for student | object | Student fields: `student_number`, optional `batch_id`, `department_id`, `guardian_profile_id` |
| `instructor` | No | object | Instructor fields: optional `employee_number`, `department_id`, `title`, `bio` |
| `admin` | No | object | Admin fields: optional `admin_type`, `department_id` |

Response fields: profile object with `id`, `auth_account_id`, `institution_id`, names, `display_name`, `avatar_url`, `status`, `metadata`, `profile_type`, `role_profile`, timestamps, and `deleted_at`.
Status behavior: `201` on success; local creation failure after account creation triggers auth account deactivation compensation.

### API-005-002 Search Profiles
Purpose: Search profiles with institution-scoped authorization.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `GET` |
| Path | `/api/users/profiles/` |
| Auth | Bearer access token with `profile.view` |
| Path parameters | None |

Query parameters:

| Parameter | Type | Purpose |
| --- | --- | --- |
| `institution_id` | UUID | Restrict profiles to one institution and authorize institution scope |
| `q` | string | Search first name, last name, or display name |
| `profile_type` | string enum | Filter by `student`, `instructor`, or `admin` |
| `status` | string enum | Filter profile lifecycle status |
| `department_id` | UUID | Filter by role-specific department |
| `batch_id` | UUID | Filter student profiles by batch |
| `sort` | string enum | Sort by name or timestamp |
| `page` | integer | Page number |
| `page_size` | integer | Page size, capped by service paginator |

Response fields: paginated profile objects.
Status behavior: `200` on success; unauthorized scopes are denied.

### API-005-003 Read Profile
Purpose: Return a profile with role-specific profile data.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `GET` |
| Path | `/api/users/profiles/<uuid>/` |
| Auth | Bearer access token with `profile.view` at profile institution scope |

Path parameters:

| Parameter | Type | Purpose |
| --- | --- | --- |
| `uuid` | UUID | User profile ID |

Response fields: profile object as described in [API-005-001](#api-005-001-create-profile).
Status behavior: `200` on success; missing, soft-deleted, or unauthorized profiles are rejected.

### API-005-004 Update Profile
Purpose: Update local profile fields and optional auth account email/phone.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `PATCH` |
| Path | `/api/users/profiles/<uuid>/` |
| Auth | Bearer access token with `profile.manage` at profile institution scope |

Path parameters:

| Parameter | Type | Purpose |
| --- | --- | --- |
| `uuid` | UUID | User profile ID |

Request body parameters: optional `email`, `phone`, base profile fields, `status`, `metadata`, and role-specific `student`, `instructor`, or `admin` payloads.
Response fields: updated profile object.
Status behavior: `200` on success; auth-service update failure returns a controlled API error.

### API-005-005 Deactivate Profile
Purpose: Deactivate a user profile and its linked auth account.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `POST` |
| Path | `/api/users/profiles/<uuid>/deactivate/` |
| Auth | Bearer access token with `profile.manage` at profile institution scope |

Path parameters:

| Parameter | Type | Purpose |
| --- | --- | --- |
| `uuid` | UUID | User profile ID |

Request body: none.
Response fields: deactivated profile object.
Status behavior: `200` on success; auth-service deactivation failure returns a controlled API error.

### API-005-006 Import Job Placeholder
Purpose: Reserve the future bulk user import endpoint with a stable not-implemented response.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `POST` |
| Path | `/api/users/import-jobs/` |
| Auth | Bearer access token with `profile.manage` |

Request body parameters:

| Parameter | Required | Type | Purpose |
| --- | --- | --- | --- |
| `institution_id` | No | UUID | Authorization scope for future import job |

Response fields:

| Field | Type | Purpose |
| --- | --- | --- |
| `code` | string | Stable error code, currently `not_implemented` |
| `detail` | string | Human-readable not-implemented message |

Status behavior: `501` after authorization succeeds.

## API-006 Institution, Department, And Batch APIs

### API-006-001 Search Institutions
Purpose: Search institution records.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `GET` |
| Path | `/api/users/institutions/` |
| Auth | Bearer access token with platform-scope `institution.manage` |

Query parameters:

| Parameter | Type | Purpose |
| --- | --- | --- |
| `q` | string | Search institution `name` or `code` |
| `status` | string enum | Filter by `active`, `suspended`, or `archived` |
| `sort` | string enum | Sort by `name`, `code`, `status`, `created_at`, or `updated_at`, with optional `-` prefix |
| `page` | integer | Page number |
| `page_size` | integer | Page size |

Response fields: paginated institution objects with `id`, `name`, `code`, `status`, `settings`, timestamps, and `deleted_at`.
Status behavior: `200` on success; platform authorization required.

### API-006-002 Create Institution
Purpose: Create an institution.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `POST` |
| Path | `/api/users/institutions/` |
| Auth | Bearer access token with platform-scope `institution.manage` |

Request body parameters:

| Parameter | Required | Type | Purpose |
| --- | --- | --- | --- |
| `name` | Yes | string | Institution name |
| `code` | Yes | string | Institution code, normalized to uppercase |
| `status` | No | string enum | Defaults to `active` |
| `settings` | No | object | Institution settings |

Response fields: institution object.
Status behavior: `201` on success; duplicate code or authorization failure is rejected.

### API-006-003 Read Institution
Purpose: Read one institution.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `GET` |
| Path | `/api/users/institutions/<uuid>/` |
| Auth | Bearer access token with platform-scope `institution.manage` |

Path parameters:

| Parameter | Type | Purpose |
| --- | --- | --- |
| `uuid` | UUID | Institution ID |

Response fields: institution object.
Status behavior: `200` on success; missing, soft-deleted, or unauthorized records are rejected.

### API-006-004 Update Institution
Purpose: Update institution fields.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `PATCH` |
| Path | `/api/users/institutions/<uuid>/` |
| Auth | Bearer access token with platform-scope `institution.manage` |

Path parameters: `uuid` institution ID.
Request body parameters: optional `name`, `code`, `status`, and `settings`.
Response fields: updated institution object.
Status behavior: `200` on success; duplicate code or authorization failure is rejected.

### API-006-005 Archive Institution
Purpose: Soft-delete an institution while preserving historical relationships.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `DELETE` |
| Path | `/api/users/institutions/<uuid>/` |
| Auth | Bearer access token with platform-scope `institution.manage` |

Path parameters: `uuid` institution ID.
Response fields: archived institution object with `status = archived` and `deleted_at`.
Status behavior: `200` on success.

### API-006-006 Search Departments
Purpose: Search department records.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `GET` |
| Path | `/api/users/departments/` |
| Auth | `institution.manage`; institution scope when `institution_id` is present, otherwise platform scope |

Query parameters:

| Parameter | Type | Purpose |
| --- | --- | --- |
| `institution_id` | UUID | Restrict to one institution and authorize that scope |
| `q` | string | Search department `name` or `code` |
| `status` | string enum | Filter by `active`, `inactive`, or `archived` |
| `sort` | string enum | Sort by `name`, `code`, `status`, `created_at`, or `updated_at`, with optional `-` prefix |
| `page` | integer | Page number |
| `page_size` | integer | Page size |

Response fields: paginated department objects with `id`, `institution_id`, `name`, `code`, `status`, timestamps, and `deleted_at`.
Status behavior: `200` on success; cross-institution or missing-scope access is denied.

### API-006-007 Create Department
Purpose: Create a department inside an institution.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `POST` |
| Path | `/api/users/departments/` |
| Auth | Bearer access token with `institution.manage` at request `institution_id` |

Request body parameters:

| Parameter | Required | Type | Purpose |
| --- | --- | --- | --- |
| `institution_id` | Yes | UUID | Owning institution |
| `name` | Yes | string | Department name |
| `code` | Yes | string | Department code, normalized to uppercase |
| `status` | No | string enum | Defaults to `active` |

Response fields: department object.
Status behavior: `201` on success; missing institution, duplicate code within institution, or authorization failure is rejected.

### API-006-008 Read Department
Purpose: Read one department.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `GET` |
| Path | `/api/users/departments/<uuid>/` |
| Auth | Bearer access token with `institution.manage` at department institution |

Path parameters: `uuid` department ID.
Response fields: department object.
Status behavior: `200` on success; missing, soft-deleted, or unauthorized records are rejected.

### API-006-009 Update Department
Purpose: Update department fields without moving it across institutions.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `PATCH` |
| Path | `/api/users/departments/<uuid>/` |
| Auth | Bearer access token with `institution.manage` at department institution |

Path parameters: `uuid` department ID.
Request body parameters: optional `name`, `code`, and `status`.
Response fields: updated department object.
Status behavior: `200` on success; duplicate code within institution or authorization failure is rejected.

### API-006-010 Archive Department
Purpose: Soft-delete a department while preserving historical relationships.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `DELETE` |
| Path | `/api/users/departments/<uuid>/` |
| Auth | Bearer access token with `institution.manage` at department institution |

Path parameters: `uuid` department ID.
Response fields: archived department object with `status = archived` and `deleted_at`.
Status behavior: `200` on success.

### API-006-011 Search Batches
Purpose: Search batch records.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `GET` |
| Path | `/api/users/batches/` |
| Auth | `institution.manage`; institution scope when `institution_id` is present, otherwise platform scope |

Query parameters:

| Parameter | Type | Purpose |
| --- | --- | --- |
| `institution_id` | UUID | Restrict to one institution and authorize that scope |
| `department_id` | UUID | Restrict to one department |
| `q` | string | Search batch `name` |
| `status` | string enum | Filter by `active`, `completed`, or `archived` |
| `sort` | string enum | Sort by `name`, `code`, `status`, `created_at`, or `updated_at`, with optional `-` prefix |
| `page` | integer | Page number |
| `page_size` | integer | Page size |

Response fields: paginated batch objects with `id`, `institution_id`, `department_id`, `name`, `start_date`, `end_date`, `status`, timestamps, and `deleted_at`.
Status behavior: `200` on success; unauthorized scopes are denied.

### API-006-012 Create Batch
Purpose: Create a batch inside an institution.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `POST` |
| Path | `/api/users/batches/` |
| Auth | Bearer access token with `institution.manage` at request `institution_id` |

Request body parameters:

| Parameter | Required | Type | Purpose |
| --- | --- | --- | --- |
| `institution_id` | Yes | UUID | Owning institution |
| `department_id` | No | UUID/null | Optional department in the same institution |
| `name` | Yes | string | Batch name |
| `start_date` | No | date/null | Batch start date |
| `end_date` | No | date/null | Batch end date; cannot be before start date |
| `status` | No | string enum | Defaults to `active` |

Response fields: batch object.
Status behavior: `201` on success; invalid institution, cross-institution department, invalid date range, or authorization failure is rejected.

### API-006-013 Read Batch
Purpose: Read one batch.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `GET` |
| Path | `/api/users/batches/<uuid>/` |
| Auth | Bearer access token with `institution.manage` at batch institution |

Path parameters: `uuid` batch ID.
Response fields: batch object.
Status behavior: `200` on success; missing, soft-deleted, or unauthorized records are rejected.

### API-006-014 Update Batch
Purpose: Update batch fields while keeping department references inside the batch institution.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `PATCH` |
| Path | `/api/users/batches/<uuid>/` |
| Auth | Bearer access token with `institution.manage` at batch institution |

Path parameters: `uuid` batch ID.
Request body parameters: optional `department_id`, `name`, `start_date`, `end_date`, and `status`.
Response fields: updated batch object.
Status behavior: `200` on success; cross-institution department, invalid date range, or authorization failure is rejected.

### API-006-015 Archive Batch
Purpose: Soft-delete a batch while preserving historical relationships.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `DELETE` |
| Path | `/api/users/batches/<uuid>/` |
| Auth | Bearer access token with `institution.manage` at batch institution |

Path parameters: `uuid` batch ID.
Response fields: archived batch object with `status = archived` and `deleted_at`.
Status behavior: `200` on success.

## API-007 Course Catalog And Metadata APIs

Related design: [API-006 Course Catalog And Metadata](api-design/API-006-course-catalog-metadata.md)
Related task: [T-006](tasks/T-006-course-catalog-metadata.md)

### API-007-001 Search Courses
Purpose: Search catalog courses.

| Item | Value |
| --- | --- |
| Service | `course-service` |
| Method | `GET` |
| Path | `/api/courses/` |
| Auth | Bearer access token with `course.view` or `course.manage` |

Query parameters:

| Parameter | Type | Purpose |
| --- | --- | --- |
| `institution_id` | UUID | Restrict to one institution and authorize that scope |
| `owner_profile_id` | UUID | Restrict to one course owner profile |
| `status` | string enum | Management filter for `draft`, `published`, `archived`, or `deleted` |
| `difficulty_level` | string enum | Filter by `beginner`, `intermediate`, or `advanced` |
| `category_id` | UUID | Filter by linked category |
| `tag_id` | UUID | Filter by linked tag |
| `q` | string | Search course title and description |
| `sort` | string enum | Sort by title, status, difficulty, published time, created time, or updated time |
| `page` | integer | Page number |
| `page_size` | integer | Page size |

Response fields: paginated course objects with core course fields, categories, tags, prerequisite course IDs, learning outcomes, timestamps, and `deleted_at`.
Status behavior: viewers see published courses only; management users may list non-published states.

### API-007-002 Create Course
Purpose: Create a draft course with catalog metadata.

| Item | Value |
| --- | --- |
| Service | `course-service` |
| Method | `POST` |
| Path | `/api/courses/` |
| Auth | Bearer access token with `course.manage` at request `institution_id` |

Request body parameters:

| Parameter | Required | Type | Purpose |
| --- | --- | --- | --- |
| `institution_id` | Yes | UUID | Owning institution |
| `owner_profile_id` | Yes | UUID | Instructor/admin owner profile reference |
| `title` | Yes | string | Course title |
| `slug` | No | string | URL slug; generated from title when omitted |
| `description` | No | string/null | Course description |
| `difficulty_level` | No | enum/null | `beginner`, `intermediate`, or `advanced` |
| `thumbnail_asset_id` | No | UUID/null | Cross-service content asset reference |
| `category_ids` | No | UUID array | Categories to attach |
| `tag_ids` | No | UUID array | Tags to attach |
| `prerequisite_course_ids` | No | UUID array | Same-institution prerequisite courses |
| `learning_outcomes` | No | object array | Ordered outcome objects with `description` and optional `position` |

Response fields: created draft course object.
Status behavior: `201` on success; invalid metadata, duplicate slug, or authorization failure is rejected. Emits `CourseCreated`.

### API-007-003 Read Course
Purpose: Read one course.

| Item | Value |
| --- | --- |
| Service | `course-service` |
| Method | `GET` |
| Path | `/api/courses/<uuid>/` |
| Auth | `course.view` for published courses; `course.manage` for draft, archived, or deleted courses |

Path parameters: `uuid` course ID.
Response fields: course object with metadata arrays.
Status behavior: published detail reads may use Redis cache; non-published reads bypass cache.

### API-007-004 Update Course
Purpose: Update course fields and replace any supplied metadata arrays.

| Item | Value |
| --- | --- |
| Service | `course-service` |
| Method | `PATCH` |
| Path | `/api/courses/<uuid>/` |
| Auth | Bearer access token with `course.manage` at current course institution and new institution when changed |

Path parameters: `uuid` course ID.
Request body parameters: optional `institution_id`, `owner_profile_id`, `title`, `slug`, `description`, `difficulty_level`, `thumbnail_asset_id`, `category_ids`, `tag_ids`, `prerequisite_course_ids`, and `learning_outcomes`.
Response fields: updated course object.
Status behavior: metadata arrays replace existing links only when supplied; cache is invalidated.

### API-007-005 Publish Course
Purpose: Publish a course into catalog discovery.

| Item | Value |
| --- | --- |
| Service | `course-service` |
| Method | `POST` |
| Path | `/api/courses/<uuid>/publish/` |
| Auth | Bearer access token with `course.manage` at course institution |

Path parameters: `uuid` course ID.
Response fields: published course object with `status = published` and `published_at`.
Status behavior: `200` on success; cache is invalidated and `CoursePublished` is emitted.

### API-007-006 Archive Course
Purpose: Archive a course and hide it from normal discovery.

| Item | Value |
| --- | --- |
| Service | `course-service` |
| Method | `POST` |
| Path | `/api/courses/<uuid>/archive/` |
| Auth | Bearer access token with `course.manage` at course institution |

Path parameters: `uuid` course ID.
Response fields: archived course object.
Status behavior: `200` on success; cache is invalidated and `CourseArchived` is emitted.

### API-007-007 Delete Course
Purpose: Soft-delete a course.

| Item | Value |
| --- | --- |
| Service | `course-service` |
| Method | `DELETE` |
| Path | `/api/courses/<uuid>/` |
| Auth | Bearer access token with `course.manage` at course institution |

Path parameters: `uuid` course ID.
Response fields: deleted course object with `status = deleted` and `deleted_at`.
Status behavior: `200` on success; cache is invalidated.

### API-007-008 Category APIs
Purpose: Manage course categories.

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/courses/categories/` | Search categories with `institution_id`, `q`, `sort`, `page`, and `page_size` | `course.view` or `course.manage` |
| `POST` | `/api/courses/categories/` | Create global or institution-scoped category | `course.manage` |
| `GET` | `/api/courses/categories/<uuid>/` | Read category | `course.view` or `course.manage` |
| `PATCH` | `/api/courses/categories/<uuid>/` | Update category name, slug, or parent | `course.manage` |
| `DELETE` | `/api/courses/categories/<uuid>/` | Delete category and category links | `course.manage` |

Request body parameters: `institution_id`, `name`, optional `slug`, and optional `parent_category_id`.
Response fields: category object with `id`, `institution_id`, `name`, `slug`, `parent_category_id`, and timestamps.

### API-007-009 Tag APIs
Purpose: Manage course tags.

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/courses/tags/` | Search tags with `institution_id`, `q`, `sort`, `page`, and `page_size` | `course.view` or `course.manage` |
| `POST` | `/api/courses/tags/` | Create global or institution-scoped tag | `course.manage` |
| `GET` | `/api/courses/tags/<uuid>/` | Read tag | `course.view` or `course.manage` |
| `PATCH` | `/api/courses/tags/<uuid>/` | Update tag name or slug | `course.manage` |
| `DELETE` | `/api/courses/tags/<uuid>/` | Delete tag and tag links | `course.manage` |

Request body parameters: `institution_id`, `name`, and optional `slug`.
Response fields: tag object with `id`, `institution_id`, `name`, `slug`, and `created_at`.

## Future APIs Not Implemented
Content upload, enrollment workflows, progress tracking, dashboards, assessment authoring, quiz attempts, assignment submissions, grading, certificates, notifications, analytics reporting, API gateway, Kafka transport, Redis architecture operations, deployment, and broader security APIs remain future task scope unless explicitly listed above.
