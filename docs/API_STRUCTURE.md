# LearnGrid LMS API Structure

Source of truth: [api-design/](api-design/README.md)
Related implementation docs: [DEVELOPMENT.md](DEVELOPMENT.md), [TASKS.md](TASKS.md)
Related implemented designs: [API-001](api-design/API-001-service-health-and-dev-stack.md) through [API-019](api-design/API-019-api-gateway.md)

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
| `pnpm dev` | Optional env `POETRY_BIN`; no CLI parameters | Start PostgreSQL, Redis, MinIO, ten backend services, and frontend with installs/migrations |
| `pnpm dev:fast` | Optional env `POETRY_BIN`; no CLI parameters | Start the stack while skipping installs and migrations |
| `pnpm dev:infra` | None | Start PostgreSQL, Redis, and MinIO |
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
| `primary_role` | string/null | Highest-precedence active role for frontend routing |
| `role_assignments` | array | Active role assignment objects with `id`, `role_code`, `role_name`, `scope_type`, `scope_id`, and `assigned_at` |

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

## API-004 User Profile APIs

### API-004-004 Create Profile
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

### API-004-005 Search Profiles
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

### API-004-006 Read Profile
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

Response fields: profile object as described in [API-004-004](#api-004-004-create-profile).
Status behavior: `200` on success; missing, soft-deleted, or unauthorized profiles are rejected.

### API-004-007 Update Profile
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

### API-004-008 Deactivate Profile
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

### API-004-009 Import Job Placeholder
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

## API-005 Institution, Department, And Batch APIs

### API-005-001 Search Institutions
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

### API-005-002 Create Institution
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

### API-005-003 Read Institution
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

### API-005-004 Update Institution
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

### API-005-005 Archive Institution
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

### API-005-006 Search Departments
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

### API-005-007 Create Department
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

### API-005-008 Read Department
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

### API-005-009 Update Department
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

### API-005-010 Archive Department
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

### API-005-011 Search Batches
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

### API-005-012 Create Batch
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

### API-005-013 Read Batch
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

### API-005-014 Update Batch
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

### API-005-015 Archive Batch
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

## API-006 Course Catalog And Metadata APIs

Related design: [API-006 Course Catalog And Metadata](api-design/API-006-course-catalog-metadata.md)
Related task: [T-006](tasks/T-006-course-catalog-metadata.md)

### API-006-001 Search Courses
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

### API-006-002 Create Course
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

### API-006-003 Read Course
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

### API-006-004 Update Course
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

### API-006-005 Publish Course
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

### API-006-006 Archive Course
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

### API-006-007 Delete Course
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

### API-006-008 Category APIs
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

### API-006-009 Tag APIs
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

## API-007 Course Structure And Versioning APIs

Related design: [API-007 Course Structure And Versioning](api-design/API-007-course-structure-versioning.md)
Related task: [T-007](tasks/T-007-course-structure-versioning.md)

### API-007-001 Read Course Structure
Purpose: Read nested modules, lessons, and topics for a course.

| Item | Value |
| --- | --- |
| Service | `course-service` |
| Method | `GET` |
| Path | `/api/courses/<uuid>/structure/` |
| Auth | `course.view` for published structure; `course.manage` for draft/archived/deleted structure |

Path parameters: `uuid` course ID.
Response fields: course identity plus ordered `modules`, nested `lessons`, and nested `topics`.
Status behavior: published reads hide draft lessons and non-published modules; management reads include active draft, published, and archived structure records.

### API-007-002 Module APIs
Purpose: Manage ordered course modules.

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/courses/<uuid>/modules/` | List modules in a course | `course.view` or `course.manage` |
| `POST` | `/api/courses/<uuid>/modules/` | Create a module | `course.manage` |
| `GET` | `/api/courses/modules/<uuid>/` | Read one module | `course.view` or `course.manage` |
| `PATCH` | `/api/courses/modules/<uuid>/` | Update a module | `course.manage` |
| `DELETE` | `/api/courses/modules/<uuid>/` | Soft-archive a module | `course.manage` |
| `POST` | `/api/courses/<uuid>/modules/reorder/` | Transactionally reorder modules | `course.manage` |

Request body parameters: `title`, `description`, optional `position`, and optional `status`.
Reorder body parameter: `module_ids`, the complete active ordered module ID list.

### API-007-003 Lesson APIs
Purpose: Manage ordered lessons and lesson publishing.

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/courses/modules/<uuid>/lessons/` | List lessons in a module | `course.view` or `course.manage` |
| `POST` | `/api/courses/modules/<uuid>/lessons/` | Create a lesson | `course.manage` |
| `GET` | `/api/courses/lessons/<uuid>/` | Read one lesson | `course.view` or `course.manage` |
| `PATCH` | `/api/courses/lessons/<uuid>/` | Update a lesson or move it within the same course | `course.manage` |
| `DELETE` | `/api/courses/lessons/<uuid>/` | Soft-archive a lesson | `course.manage` |
| `POST` | `/api/courses/lessons/<uuid>/publish/` | Publish a lesson and emit `LessonPublished` | `course.manage` |
| `POST` | `/api/courses/modules/<uuid>/lessons/reorder/` | Transactionally reorder lessons | `course.manage` |

Request body parameters: `module_id` on update, `title`, `summary`, optional `position`, optional `status`, and optional `content_asset_id`.
Reorder body parameter: `lesson_ids`, the complete active ordered lesson ID list.

### API-007-004 Topic APIs
Purpose: Manage ordered lesson topics.

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/courses/lessons/<uuid>/topics/` | List topics in a lesson | `course.view` or `course.manage` |
| `POST` | `/api/courses/lessons/<uuid>/topics/` | Create a topic | `course.manage` |
| `GET` | `/api/courses/topics/<uuid>/` | Read one topic | `course.view` or `course.manage` |
| `PATCH` | `/api/courses/topics/<uuid>/` | Update a topic | `course.manage` |
| `DELETE` | `/api/courses/topics/<uuid>/` | Delete a topic | `course.manage` |
| `POST` | `/api/courses/lessons/<uuid>/topics/reorder/` | Transactionally reorder topics | `course.manage` |

Request body parameters: `title`, optional `position`, and optional `content_asset_id`.
Reorder body parameter: `topic_ids`, the complete ordered topic ID list.

### API-007-005 Revision APIs
Purpose: Preserve course structure snapshots.

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/courses/<uuid>/revisions/` | List revision snapshots | `course.manage` |
| `POST` | `/api/courses/<uuid>/revisions/` | Create a revision snapshot | `course.manage` |
| `GET` | `/api/courses/revisions/<uuid>/` | Read one revision snapshot | `course.manage` |

Request body parameters: optional `created_by_profile_id`.
Response fields: `id`, `course_id`, `version_number`, `snapshot`, `created_by_profile_id`, and `created_at`.

## API-008 Content Upload, Storage, And Access APIs

Related design: [API-008 Content Upload, Storage, And Access](api-design/API-008-content-upload-storage-access.md)

### API-008-001 Search Content Assets
Purpose: Search content assets with management or view-scoped authorization.

| Item | Value |
| --- | --- |
| Service | `content-service` |
| Method | `GET` |
| Path | `/api/content/assets/` |
| Auth | Bearer access token with `content.manage` or `content.view` at `institution_id` |

Query parameters:

| Parameter | Type | Purpose |
| --- | --- | --- |
| `institution_id` | UUID | Restrict assets to one institution and authorize that scope |
| `owner_profile_id` | UUID | Restrict assets to one owner profile |
| `asset_type` | string enum | Filter by `video`, `pdf`, `document`, `image`, `link`, or `assignment_resource` |
| `status` | string enum | Filter by `draft`, `published`, `deleted`, or `quarantined` |
| `q` | string | Search asset title |
| `sort` | string enum | Sort by title, type, status, created time, or updated time, with optional `-` prefix |
| `page` | integer | Page number |
| `page_size` | integer | Page size, maximum `100` |

Response fields: paginated assets with `id`, `institution_id`, `owner_profile_id`, `asset_type`, `title`, `status`, `metadata`, `file_metadata`, timestamps, and `deleted_at`.
Status behavior: `200` on success; unauthorized scopes are denied.

### API-008-002 Create Content Asset
Purpose: Register content metadata for a link asset or an already-uploaded MinIO object.

| Item | Value |
| --- | --- |
| Service | `content-service` |
| Method | `POST` |
| Path | `/api/content/assets/` |
| Auth | Bearer access token with `content.manage` at request `institution_id` |

Request body parameters:

| Parameter | Required | Type | Purpose |
| --- | --- | --- | --- |
| `institution_id` | Yes | UUID | Owning institution |
| `owner_profile_id` | Yes | UUID | Owning profile reference |
| `asset_type` | Yes | string enum | Asset type |
| `title` | Yes | string | Asset title |
| `metadata` | No | object | Flexible metadata |
| `file` | Required unless `asset_type=link` | object | File metadata payload |
| `file.storage_provider` | No | string | Must be absent or `minio` |
| `file.bucket_name` | No | string | Defaults to `learngrid-content` |
| `file.object_key` | Yes | string | Existing MinIO object key |
| `file.file_name` | Yes | string | Original/display file name |
| `file.mime_type` | Yes | string | MIME type validated against service allow-list |
| `file.file_size_bytes` | Yes | integer | File size validated against service max |
| `file.checksum_sha256` | No | string/null | SHA-256 checksum hex string |

Response fields: created asset object with nested `file_metadata`.
Status behavior: `201` on success; unsupported MIME type, oversized file, non-MinIO provider, missing MinIO object, mismatched object metadata, missing file metadata, or authorization failure is rejected.

### API-008-010 Create Presigned Upload
Purpose: Create a draft asset and return a MinIO presigned PUT URL for direct browser upload.

| Item | Value |
| --- | --- |
| Service | `content-service` |
| Method | `POST` |
| Path | `/api/content/assets/uploads/presigned/` |
| Auth | Bearer access token with `content.manage` at request `institution_id` |

Request body parameters: `institution_id`, `owner_profile_id`, `asset_type`, `title`, optional `metadata`, `file_name`, `mime_type`, `file_size_bytes`, and optional `checksum_sha256`.
Response fields: `asset`, generated `object_key`, `upload_url`, `upload_headers`, and `expires_at`.
Status behavior: `201` on success; link assets, invalid file type/size, or unauthorized scopes are rejected. The created asset has `metadata.upload_status = pending`.

### API-008-011 Complete Presigned Upload
Purpose: Verify the uploaded MinIO object and finalize initial version metadata.

| Item | Value |
| --- | --- |
| Service | `content-service` |
| Method | `POST` |
| Path | `/api/content/assets/<uuid>/uploads/complete/` |
| Auth | Bearer access token with `content.manage` at asset institution |

Path parameters: `uuid` asset ID.
Request body parameters: optional `checksum_sha256`.
Response fields: asset object with `metadata.upload_status = complete`.
Status behavior: `200` on success; missing MinIO object, size mismatch, MIME mismatch, missing file metadata, or unauthorized access is rejected.

### API-008-012 Proxy Upload
Purpose: Upload a multipart file through content-service into MinIO.

| Item | Value |
| --- | --- |
| Service | `content-service` |
| Method | `POST` |
| Path | `/api/content/assets/uploads/proxy/` |
| Auth | Bearer access token with `content.manage` at request `institution_id` |

Multipart body parameters: `institution_id`, `owner_profile_id`, `asset_type`, `title`, optional `metadata`, and required `file`.
Response fields: created asset object with nested MinIO file metadata and SHA-256 checksum.
Status behavior: `201` on success; link assets, invalid file type/size, MinIO write failure, or authorization failure is rejected without creating DB metadata.

### API-008-003 Read Content Asset
Purpose: Read one asset, including soft-deleted metadata when directly addressed.

| Item | Value |
| --- | --- |
| Service | `content-service` |
| Method | `GET` |
| Path | `/api/content/assets/<uuid>/` |
| Auth | Bearer access token with `content.view` at asset institution |

Path parameters: `uuid` asset ID.
Response fields: asset object with nested file metadata.
Status behavior: `200` on success; missing or unauthorized assets are rejected.

### API-008-004 Update Content Asset
Purpose: Update mutable asset metadata.

| Item | Value |
| --- | --- |
| Service | `content-service` |
| Method | `PATCH` |
| Path | `/api/content/assets/<uuid>/` |
| Auth | Bearer access token with `content.manage` at asset institution |

Path parameters: `uuid` asset ID.
Request body parameters: optional `asset_type`, `title`, and `metadata`.
Response fields: updated asset object.
Status behavior: `200` on success; soft-deleted assets are not updateable.

### API-008-005 Delete Content Asset
Purpose: Soft-delete an asset and emit the local content-deleted event.

| Item | Value |
| --- | --- |
| Service | `content-service` |
| Method | `DELETE` |
| Path | `/api/content/assets/<uuid>/` |
| Auth | Bearer access token with `content.manage` at asset institution |

Path parameters: `uuid` asset ID.
Response fields: deleted asset object with `status = deleted` and `deleted_at`.
Status behavior: `200` on success.

### API-008-006 Publish Content Asset
Purpose: Mark an asset as published and emit the local content-published event.

| Item | Value |
| --- | --- |
| Service | `content-service` |
| Method | `POST` |
| Path | `/api/content/assets/<uuid>/publish/` |
| Auth | Bearer access token with `content.manage` at asset institution |

Path parameters: `uuid` asset ID.
Request body: none.
Response fields: asset object with `status = published`.
Status behavior: `200` on success.

### API-008-007 Content Permission APIs
Purpose: List and create asset-level content grants.

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/content/assets/<uuid>/permissions/` | List grants for one asset | `content.manage` |
| `POST` | `/api/content/assets/<uuid>/permissions/` | Create a content grant | `content.manage` |

Path parameters: `uuid` asset ID.
Create body parameters: `grantee_type` enum `profile`, `course`, `institution`, or `role`; `grantee_id` UUID; optional `permission` enum `view`, `download`, or `manage`; optional `expires_at`.
Response fields: permission object with `id`, `content_asset_id`, `grantee_type`, `grantee_id`, `permission`, `expires_at`, and `created_at`.
Status behavior: `200` for list, `201` for create; duplicate grants or unauthorized access are rejected.

### API-008-008 Signed Access APIs
Purpose: Issue and resolve token-hashed signed access for secure downloads.

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `POST` | `/api/content/assets/<uuid>/access/` | Create a signed access record | Bearer token with `content.view` plus owner/grant check |
| `GET` | `/api/content/download/<uuid>/?token=...` | Resolve signed access metadata | Signed token query parameter |

Create path parameters: `uuid` asset ID.
Create body parameters: `requested_by_profile_id` UUID.
Create response fields: `access_id`, `access_token`, `download_url`, `access_url`, and `expires_at`.
Download path parameters: `uuid` signed access record ID.
Download query parameters: required `token` raw signed token.
Download response fields: `asset_id`, `content_asset_id`, `title`, `object_key`, `bucket_name`, `storage_provider`, `file_name`, `mime_type`, MinIO `download_url`, and `expires_at`.
Status behavior: `201` for signed access creation and `200` for valid resolution; expired, used, missing, or invalid tokens are rejected. Only token hashes are stored.

### API-008-009 Content Version APIs
Purpose: List and create content version metadata.

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/content/assets/<uuid>/versions/` | List versions for one asset | `content.manage` |
| `POST` | `/api/content/assets/<uuid>/versions/` | Create the next version metadata record | `content.manage` |

Path parameters: `uuid` asset ID.
Create body parameters: `created_by_profile_id` UUID and optional `change_note`.
Response fields: version objects with `id`, `content_asset_id`, `version_number`, `file_metadata_id`, `change_note`, `created_by_profile_id`, and `created_at`.
Status behavior: `200` for list and `201` for create.

Storage note: [OD-002](KNOWN_ISSUES.md#od-002-object-storage-selection) is resolved with MinIO as the only supported object storage provider. [OD-006](KNOWN_ISSUES.md#od-006-video-delivery-strategy) remains open for video delivery strategy.

## API-009 Enrollment And Access Management APIs

Related design: [API-009 Enrollment And Access Management](api-design/API-009-enrollment-access-management.md)

### API-009-001 Search Enrollments
Purpose: Search enrollment records.

| Item | Value |
| --- | --- |
| Service | `enrollment-service` |
| Method | `GET` |
| Path | `/api/enrollments/` |
| Auth | Bearer access token with `enrollment.view` at `institution_id` when provided |

Query parameters:

| Parameter | Type | Purpose |
| --- | --- | --- |
| `student_profile_id` | UUID | Restrict enrollments to one student |
| `course_id` | UUID | Restrict enrollments to one course |
| `institution_id` | UUID | Restrict enrollments to one institution and authorize that scope |
| `status` | string enum | Filter by `active`, `completed`, `expired`, `cancelled`, or `suspended` |
| `sort` | string enum | Sort by status, created time, or updated time, with optional `-` prefix |
| `page` | integer | Page number |
| `page_size` | integer | Page size, maximum `100` |

Response fields: paginated enrollment objects with `id`, `student_profile_id`, `course_id`, `institution_id`, `status`, `enrolled_by_profile_id`, `enrolled_at`, `completed_at`, `expires_at`, `created_at`, and `updated_at`.
Status behavior: `200` on success.

### API-009-002 Create Enrollment
Purpose: Enroll one student profile in one course and create active access.

| Item | Value |
| --- | --- |
| Service | `enrollment-service` |
| Method | `POST` |
| Path | `/api/enrollments/` |
| Auth | Bearer access token with `enrollment.manage` at request `institution_id` |

Request body parameters: `student_profile_id` UUID, `course_id` UUID, `institution_id` UUID, optional `enrolled_by_profile_id`, and optional `expires_at`.
Response fields: created enrollment object.
Status behavior: `201` on success; duplicate student/course enrollment is rejected.

### API-009-003 Read Enrollment
Purpose: Read one enrollment record.

| Item | Value |
| --- | --- |
| Service | `enrollment-service` |
| Method | `GET` |
| Path | `/api/enrollments/<uuid>/` |
| Auth | Bearer access token with `enrollment.view` at enrollment institution |

Path parameters: `uuid` enrollment ID.
Response fields: enrollment object.
Status behavior: `200` on success; missing or unauthorized records are rejected.

### API-009-004 Transition Enrollment
Purpose: Change enrollment status and synchronize access grants.

| Item | Value |
| --- | --- |
| Service | `enrollment-service` |
| Method | `POST` |
| Path | `/api/enrollments/<uuid>/transition/` |
| Auth | Bearer access token with `enrollment.manage` at enrollment institution |

Path parameters: `uuid` enrollment ID.
Request body parameters: required `status` enum `active`, `completed`, `expired`, `cancelled`, or `suspended`; optional `changed_by_profile_id`; optional `reason`.
Response fields: updated enrollment object.
Status behavior: `200` on success; access grants are activated, expired, revoked, or suspended according to the target status.

### API-009-005 Enrollment History
Purpose: Read status history for one enrollment.

| Item | Value |
| --- | --- |
| Service | `enrollment-service` |
| Method | `GET` |
| Path | `/api/enrollments/<uuid>/history/` |
| Auth | Bearer access token with `enrollment.view` at enrollment institution |

Path parameters: `uuid` enrollment ID.
Response fields: list of history records with `id`, `enrollment_id`, `from_status`, `to_status`, `changed_by_profile_id`, `reason`, and `created_at`.
Status behavior: `200` on success.

### API-009-006 Access Check
Purpose: Check whether a student has active access to a course.

| Item | Value |
| --- | --- |
| Service | `enrollment-service` |
| Method | `GET` |
| Path | `/api/enrollments/access/check/` |
| Auth | Bearer access token with `enrollment.view` |

Query parameters: required `student_profile_id` UUID and `course_id` UUID.
Response fields: `allowed` boolean.
Status behavior: `200` on success.

### API-009-007 Batch Enrollment Jobs
Purpose: List or create batch enrollment jobs.

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/enrollments/batch-enrollments/` | List batch jobs | `enrollment.view` |
| `POST` | `/api/enrollments/batch-enrollments/` | Create a batch enrollment job | `enrollment.manage` |

Create body parameters: `batch_id`, `course_id`, `institution_id`, `requested_by_profile_id`, and `student_profile_ids`.
Response fields: job object with `id`, `batch_id`, `course_id`, `requested_by_profile_id`, `status`, `summary`, `created_at`, and `updated_at`.
Status behavior: `200` for list and `201` for create; creation also writes concrete enrollment records for supplied students.

### API-009-008 Cohort Enrollment Jobs
Purpose: List or create cohort enrollment jobs.

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/enrollments/cohort-enrollments/` | List cohort jobs | `enrollment.view` |
| `POST` | `/api/enrollments/cohort-enrollments/` | Create a cohort enrollment job | `enrollment.manage` |

Create body parameters: `cohort_id`, `course_id`, `institution_id`, `requested_by_profile_id`, and `student_profile_ids`.
Response fields: job object with `id`, `cohort_id`, `course_id`, `requested_by_profile_id`, `status`, `summary`, `created_at`, and `updated_at`.
Status behavior: `200` for list and `201` for create; creation also writes concrete enrollment records for supplied students.

## API-010 Learning Progress Tracking APIs

Related design: [API-010 Learning Progress Tracking](api-design/API-010-learning-progress-tracking.md)

### API-010-001 Update Lesson Progress
Purpose: Upsert lesson progress and recalculate course progress.

| Item | Value |
| --- | --- |
| Service | `progress-service` |
| Method | `POST` |
| Path | `/api/progress/lessons/` |
| Auth | Bearer access token with `progress.manage` at request `course_id` |

Request body parameters: `student_profile_id`, `course_id`, `lesson_id`, optional `status` enum `not_started`, `in_progress`, or `completed`, optional `view_increment`, optional `total_lessons`, and optional `total_assessments`.
Response fields: lesson progress object with `id`, `student_profile_id`, `course_id`, `lesson_id`, `status`, `view_count`, `first_viewed_at`, `completed_at`, and `updated_at`.
Status behavior: `200` on create or update.

### API-010-002 Update Video Progress
Purpose: Upsert video progress and recalculate course progress.

| Item | Value |
| --- | --- |
| Service | `progress-service` |
| Method | `POST` |
| Path | `/api/progress/videos/` |
| Auth | Bearer access token with `progress.manage` at request `course_id` |

Request body parameters: `student_profile_id`, `content_asset_id`, `course_id`, optional `last_position_seconds`, optional `duration_seconds`, optional `percent_complete`, optional `total_lessons`, and optional `total_assessments`.
Response fields: video progress object with `id`, `student_profile_id`, `content_asset_id`, `course_id`, playback fields, `completed_at`, and `updated_at`.
Status behavior: `200` on create or update; percent values are constrained to `0` through `100`.

### API-010-003 Update Assessment Progress
Purpose: Upsert assessment progress and recalculate course progress.

| Item | Value |
| --- | --- |
| Service | `progress-service` |
| Method | `POST` |
| Path | `/api/progress/assessments/` |
| Auth | Bearer access token with `progress.manage` at request `course_id` |

Request body parameters: `student_profile_id`, `assessment_id`, `course_id`, optional `status` enum `not_started`, `started`, `submitted`, or `graded`, optional `attempt_increment`, optional `total_lessons`, and optional `total_assessments`.
Response fields: assessment progress object with `id`, `student_profile_id`, `assessment_id`, `course_id`, `status`, `attempt_count`, `last_submitted_at`, and `updated_at`.
Status behavior: `200` on create or update.

### API-010-004 List Course Progress
Purpose: List course progress summaries.

| Item | Value |
| --- | --- |
| Service | `progress-service` |
| Method | `GET` |
| Path | `/api/progress/courses/` |
| Auth | Bearer access token with `progress.view`; course-scoped when `course_id` is provided |

Query parameters: optional `student_profile_id`, optional `course_id`, and optional `status`.
Response fields: list of course progress objects with `id`, `student_profile_id`, `course_id`, `completion_percent`, `lessons_completed`, `assessments_completed`, `status`, `completed_at`, and `updated_at`.
Status behavior: `200` on success.

### API-010-005 Read Course Progress
Purpose: Read one course progress summary.

| Item | Value |
| --- | --- |
| Service | `progress-service` |
| Method | `GET` |
| Path | `/api/progress/courses/<uuid>/` |
| Auth | Bearer access token with `progress.view` at progress course |

Path parameters: `uuid` course progress record ID.
Response fields: course progress object.
Status behavior: `200` on success.

### API-010-006 Progress Event APIs
Purpose: List processed events or ingest a progress event idempotently.

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/progress/events/` | List processed progress events | `progress.view` |
| `POST` | `/api/progress/events/` | Ingest one progress event | `progress.manage` at `payload.course_id` |

Create body parameters: `event_id` UUID, `event_type` enum `LessonViewed`, `VideoCompleted`, `QuizSubmitted`, or `AssignmentSubmitted`, `aggregate_id` UUID, and `payload` object.
Response fields: `status` string, currently `processed` or `duplicate`, and `event_id`.
Status behavior: duplicate `event_id` returns `status = duplicate`; new supported events update progress and return `status = processed`.

## API-011 Dashboards And Portals APIs

Related design: [API-011 Dashboards And Portals](api-design/API-011-dashboards-portals.md)

### API-011-001 Frontend Portal Routes
| Route | Purpose | Auth behavior |
| --- | --- | --- |
| `/login` | Sign in through auth-service token issue | Public |
| `/dashboard` | Role-aware portal redirect | Requires stored access token plus session/profile lookup |
| `/dashboard/student` | Student portal | `student` primary role |
| `/dashboard/instructor` | Instructor portal | `instructor` or `teaching_assistant` primary role |
| `/dashboard/admin` | Admin portal | `super_admin` or `institution_admin` primary role |
| `/dashboard/no-access` | Unsupported-role state | Public fallback |

### API-011-002 Current Profile
Purpose: Resolve the authenticated account to a user-service profile.

| Item | Value |
| --- | --- |
| Service | `user-service` |
| Method | `GET` |
| Path | `/api/users/profiles/me/` |
| Auth | Bearer access token plus `profile.view` at profile institution/platform scope |
| Path parameters | None |
| Query parameters | None |
| Request body | None |
| Response fields | User profile object matching `/api/users/profiles/<uuid>/` |
| Status behavior | `200` on success; `404` if no active profile exists; authorization failures deny access |

### API-011-003 Dashboard APIs
| Method | Path | Service | Purpose | Auth |
| --- | --- | --- | --- | --- |
| `GET` | `/api/analytics/dashboards/student/` | `analytics-service` | Current student dashboard | Bearer token, student profile, and `profile.view` |
| `GET` | `/api/analytics/dashboards/instructor/` | `analytics-service` | Current instructor dashboard | Bearer token, instructor/admin profile, and `analytics.view` |
| `GET` | `/api/analytics/dashboards/admin/?institution_id=<uuid>` | `analytics-service` | Institution dashboard | Bearer token with institution-scoped `analytics.view` |
| `GET` | `/api/analytics/dashboards/admin/system/` | `analytics-service` | Platform dashboard | Bearer token with platform `analytics.view` |

Student response fields: `portal`, `profile`, `institution_id`, `aggregate`, `active_courses`, `completed_lessons`, `pending_assessments`, `grades`, `upcoming_deadlines`, and `summary`.

Instructor response fields: `portal`, `profile`, `institution_id`, `aggregate`, `learner_engagement`, `progress_distribution`, `assessment_status`, `course_summaries`, and `summary`.

Admin response fields: `portal`, `profile`, `institution_id`, `aggregate`, `active_users`, `enrollments`, `completion_rates`, `assessment_results`, `system_usage`, and `summary`.

If no aggregate exists, dashboard APIs return `200` with `aggregate = null`, empty arrays, and zeroed summary values.

### API-011-004 Analytics Events And Report Snapshots
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `POST` | `/api/analytics/events/ingest/` | Idempotently store one analytics event | `analytics.view` at institution/platform scope |
| `GET` | `/api/analytics/reports/snapshots/` | List report snapshots with optional `institution_id` and `report_type` filters | `analytics.view` at institution/platform scope |
| `POST` | `/api/analytics/reports/snapshots/` | Create a report snapshot | `analytics.view` at institution/platform scope |

Event body parameters: `event_id`, `event_type`, `producer_service`, `aggregate_id`, optional `institution_id`, `occurred_at`, and optional `payload`. Duplicate `event_id` returns `created = false`.

Report snapshot body parameters: optional `institution_id`, `report_type`, optional `parameters`, and optional `result_payload`. `generated_by_profile_id` is resolved from `/api/users/profiles/me/`.

## API-012 Assessment Authoring APIs

Related design: [API-012 Assessment Authoring](api-design/API-012-assessment-authoring.md)

### API-012-001 Question Banks And Questions
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/assessments/question-banks/` | Search question banks with `institution_id`, `owner_profile_id`, `q`, `sort`, `page`, and `page_size` | `assessment.view` |
| `POST` | `/api/assessments/question-banks/` | Create a question bank | `assessment.manage` at institution |
| `GET/PATCH/DELETE` | `/api/assessments/question-banks/<uuid>/` | Read, update, or soft-delete a bank | `assessment.view/manage` |
| `GET` | `/api/assessments/question-banks/<uuid>/questions/` | Search questions with `question_type`, `status`, `q`, `sort`, `page`, and `page_size` | `assessment.view` |
| `POST` | `/api/assessments/question-banks/<uuid>/questions/` | Create a supported question | `assessment.manage` |
| `GET/PATCH/DELETE` | `/api/assessments/questions/<uuid>/` | Read, update, or soft-delete a question | `assessment.view/manage` |

Question body parameters: `question_type`, `prompt`, optional `choices`, optional `correct_answer`, optional `points`, and optional `status`. Supported types are `multiple_choice`, `multiple_select`, `true_false`, `short_answer`, `essay`, and `file_upload`; `coding` is schema-reserved and rejected.

### API-012-002 Assessment Authoring
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/assessments/` | Search assessments with course/type/status/window filters | `assessment.view`; non-published reads require manage |
| `POST` | `/api/assessments/` | Create quiz, exam, or assignment shell | `assessment.manage` |
| `GET/PATCH/DELETE` | `/api/assessments/<uuid>/` | Read, update, or archive one assessment | `assessment.view/manage` |
| `PUT` | `/api/assessments/<uuid>/questions/` | Replace ordered quiz/exam questions | `assessment.manage` |
| `POST` | `/api/assessments/<uuid>/publish/` | Publish assessment and emit `AssessmentPublished` | `assessment.manage` |
| `POST` | `/api/assessments/<uuid>/close/` | Close assessment and emit `AssessmentClosed` | `assessment.manage` |

Assessment body parameters: `course_id`, optional `lesson_id`, `created_by_profile_id`, `assessment_type`, `title`, optional `description`, optional `available_from`, optional `available_until`, optional `quiz_config`, optional `assignment_config`, and optional ordered `questions`.

## API-013 Quiz Attempts And Exams APIs

Related design: [API-013 Quiz Attempts And Exams](api-design/API-013-quiz-attempts-exams.md)

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `POST` | `/api/assessments/<uuid>/attempts/start/` | Start a quiz/exam attempt | `assessment.view`, student profile, active enrollment |
| `GET` | `/api/assessments/attempts/<uuid>/` | Read attempt, saved answers, ordered student questions, and deadline | Attempt owner or `assessment.manage` |
| `PUT` | `/api/assessments/attempts/<uuid>/answers/` | Upsert durable answer payloads | Attempt owner with `assessment.view` |
| `POST` | `/api/assessments/attempts/<uuid>/submit/` | Submit an attempt and emit `QuizSubmitted` | Attempt owner with `assessment.view` |
| `POST` | `/api/assessments/attempts/<uuid>/auto-submit/` | Mark attempt as auto-submitted | Attempt owner with `assessment.view` |

Attempt start/detail responses include `attempt`, `questions`, and `deadline_at`. Student question objects omit `correct_answer`. Attempt start enforces published status, availability windows, active enrollment, max attempts, and time limits. Randomized question order is persisted in `submission_audit_logs`.

## API-014 Assignment Submissions APIs

Related design: [API-014 Assignment Submissions](api-design/API-014-assignment-submissions.md)

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/assessments/assignments/<uuid>/submissions/` | List assignment submissions with `student_profile_id` and `status` filters | Owner or `submission.view` |
| `POST` | `/api/assessments/assignments/<uuid>/submissions/` | Save a draft or submit assignment work | Student profile, `assessment.view`, active enrollment |
| `GET` | `/api/assessments/submissions/<uuid>/` | Read one assignment submission | Owner or `submission.view/manage` |
| `PATCH` | `/api/assessments/submissions/<uuid>/` | Update an own draft submission | Owner only |
| `POST` | `/api/assessments/submissions/<uuid>/submit/` | Finalize a draft and emit `AssignmentSubmitted` | Owner only |
| `POST` | `/api/assessments/submissions/<uuid>/mark-graded/` | Mark submission graded after grade publication | `submission.manage` |

Submission body parameters: optional `submission_text`, optional `attachment_asset_id`, and optional `submit`. Create requires text or attachment. Attachment UUIDs are validated through content-service. Late submissions are rejected unless `allow_late_submission=true`, and accepted late submissions use status `late`.

## API-015 Grading, Results, And Audit APIs

Related design: [API-015 Grading, Results, And Audit](api-design/API-015-grading-results-audit.md)

### API-015-001 Assessment Grading Sources
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/assessments/grading/quiz-attempts/<uuid>/` | Return grading-safe quiz attempt metadata | `grade.manage` scoped to course/institution |
| `GET` | `/api/assessments/grading/assignment-submissions/<uuid>/` | Return grading-safe assignment submission metadata | `grade.manage` scoped to course/institution |

### API-015-002 Grading Service
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET/POST` | `/api/grading/rules/` | List or create grading rules | `grade.view/manage` |
| `GET/PATCH` | `/api/grading/rules/<uuid>/` | Read or update one grading rule | `grade.view/manage` |
| `GET` | `/api/grading/records/` | List grade records with filters | `grade.view` |
| `GET` | `/api/grading/records/<uuid>/` | Read one grade record with history and reviews | `grade.view` |
| `POST` | `/api/grading/records/calculate/` | Calculate an objective quiz grade from assessment-service source data | `grade.manage` |
| `POST` | `/api/grading/records/manual-reviews/` | Create a pending manual review | `grade.manage` |
| `POST` | `/api/grading/manual-reviews/<uuid>/complete/` | Complete manual review with score and feedback | `grade.manage` |
| `POST` | `/api/grading/records/<uuid>/override/` | Override score with required `change_reason` | `grade.manage` |
| `POST` | `/api/grading/records/<uuid>/publish/` | Publish a result and emit `GradePublished` | `grade.manage` |
| `GET` | `/api/grading/results/` | List published results | Owning student or `grade.view` |
| `GET` | `/api/grading/results/<uuid>/` | Read one published result | Owning student or `grade.view` |

Grading request bodies use rule fields (`course_id`, optional `assessment_id`, `rule_type`, `configuration`, `created_by_profile_id`), calculation fields (`submission_type`, `submission_id`, optional `rule_id`), manual review fields (`submission_type`, `submission_id`, optional `reviewer_profile_id`), completion fields (`score`, optional `feedback`), override fields (`score`, optional `max_score`, required `change_reason`), and publish fields (`published_feedback`). Remote assessment, course, or user-service failures return controlled `502` responses.

## API-016 Certificates APIs

Related design: [API-016 Certificates](api-design/API-016-certificates.md)

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/grading/certificates/eligibility/` | List eligibility records with filters | `grade.view` |
| `GET` | `/api/grading/certificates/eligibility/<uuid>/` | Read one eligibility record | `grade.view` |
| `POST` | `/api/grading/certificates/eligibility/evaluate/` | Evaluate eligibility and auto-issue a certificate when eligible | `grade.manage` |
| `GET` | `/api/grading/certificates/` | List certificates with `student_profile_id`, `course_id`, and `include_revoked` filters | Owning student or `grade.view` |
| `GET` | `/api/grading/certificates/<uuid>/` | Read one certificate | Owning student or `grade.view` |
| `PATCH` | `/api/grading/certificates/<uuid>/` | Update optional `certificate_asset_id` | `grade.manage` |
| `POST` | `/api/grading/certificates/<uuid>/revoke/` | Revoke a certificate by setting `revoked_at` | `grade.manage` |

Eligibility evaluation requires completed course progress from progress-service and passing published-grade percentage from grading-service. The threshold uses `grading_rules.configuration.certificate_min_percent` when present, otherwise `GRADING_CERTIFICATE_DEFAULT_PASS_PERCENT=70`. Certificate responses include `valid`, which is false after revocation.

## API-017 Notifications APIs

Related design: [API-017 Notifications](api-design/API-017-notifications.md)

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET/POST` | `/api/notifications/templates/` | List or upsert notification templates | `notification.view/manage` |
| `GET/PATCH` | `/api/notifications/templates/<uuid>/` | Read or update one template | `notification.view/manage` |
| `GET` | `/api/notifications/` | List notifications with `recipient_profile_id`, `event_type`, `unread`, `include_deleted`, and `sort` filters | Owning profile or `notification.view` |
| `GET` | `/api/notifications/<uuid>/` | Read one notification | Owning profile or `notification.view` |
| `POST` | `/api/notifications/<uuid>/read/` | Mark one notification read | Owning profile or `notification.view` |
| `POST` | `/api/notifications/<uuid>/unread/` | Mark one notification unread | Owning profile or `notification.view` |
| `POST` | `/api/notifications/read-all/` | Mark current profile's unread notifications read | Owning profile |
| `GET/POST` | `/api/notifications/preferences/` | List or upsert notification preferences | Owning profile or `notification.manage` |
| `GET` | `/api/notifications/delivery-attempts/` | List delivery attempts | `notification.view` |
| `GET` | `/api/notifications/delivery-attempts/<uuid>/` | Read one delivery attempt | `notification.view` |
| `POST` | `/api/notifications/events/ingest/` | Ingest `StudentEnrolled`, `AssignmentDueSoon`, `GradePublished`, or `CourseCompleted` idempotently | `notification.manage` |

Event ingestion stores `payload.source_event_id` for idempotency and returns `processed`, `duplicate`, or `skipped`. In-app delivery creates `delivery_attempts` with `sent` or `failed`; email, SMS, and push remain future delivery placeholders.

## API-018 Search, Reporting, And Analytics APIs

Related design: [API-018 Search, Reporting, And Analytics](api-design/API-018-search-reporting-analytics.md)

### API-018-001 Search And Indexing
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/analytics/search/` | Search all permitted resource types with resource-specific authorization | Resource-specific view permissions |
| `GET` | `/api/analytics/search/courses/` | Search course index records | `course.view` |
| `GET` | `/api/analytics/search/users/` | Search user index records | `profile.view` |
| `GET` | `/api/analytics/search/enrollments/` | Search enrollment index records | `enrollment.view` |
| `GET` | `/api/analytics/search/assessments/` | Search assessment index records | `assessment.view` |
| `GET` | `/api/analytics/search/submissions/` | Search submission index records | `submission.view` |
| `POST` | `/api/analytics/search/index-records/` | Upsert a search index record | `analytics.view` |
| `DELETE` | `/api/analytics/search/index-records/<resource_type>/<uuid>/` | Delete a search index record | Platform `analytics.view` |

Search query parameters: `q`, `institution_id`, `resource_type`, `status`, `course_id`,
`profile_type`, `assessment_type`, `submission_status`, `sort`, `page`, and `page_size`. Upsert
body parameters: `resource_type`, `resource_id`, optional `institution_id`, `search_text`, and
optional `metadata`.

### API-018-002 Aggregates, Metrics, And Reports
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET/POST` | `/api/analytics/dashboards/aggregates/` | List or upsert institution/platform dashboard aggregates | `analytics.view` |
| `GET/POST` | `/api/analytics/usage-metrics/` | List or create usage metric records | `analytics.view` |
| `POST` | `/api/analytics/reports/generate/` | Generate and save a report snapshot from `analytics_db` | `analytics.view` |

Generated report types: `active_users`, `enrollments`, `completion_rates`, `assessment_results`,
and `system_usage`. Report responses are `report_snapshots` records with `result_payload.summary`.

## API-019 API Gateway

Related design: [API-019 API Gateway](api-design/API-019-api-gateway.md)

| Gateway URL or prefix | Purpose |
| --- | --- |
| `http://127.0.0.1:8080` | Local HTTP gateway; redirects to HTTPS |
| `https://127.0.0.1:8443` | Local HTTPS gateway with self-signed TLS |
| `/gateway/health` | Gateway health response |
| `/api/auth/` | Routes to auth-service |
| `/api/users/` | Routes to user-service |
| `/api/courses/` | Routes to course-service |
| `/api/content/` | Routes to content-service |
| `/api/enrollments/` | Routes to enrollment-service |
| `/api/progress/` | Routes to progress-service |
| `/api/assessments/` | Routes to assessment-service |
| `/api/grading/` | Routes to grading-service |
| `/api/grades/` | Alias rewritten to `/api/grading/` |
| `/api/notifications/` | Routes to notification-service |
| `/api/analytics/` | Routes to analytics-service |
| `/api/v1/...` | Rewrites to current `/api/...` paths |

Nginx terminates TLS, emits JSON request logs, forwards request IDs, applies local-origin CORS,
rate limits API traffic, and rejects oversized requests above `20m`.

## Future APIs Not Implemented
Kafka transport, Redis architecture operations, deployment, and broader security APIs remain future task scope unless explicitly listed above.
