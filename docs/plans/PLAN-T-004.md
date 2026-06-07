# T-004 User And Profile Management Plan

## Summary
Implement T-004 as the first real `user-service` domain workflow. `user-service` will own profile, institution support, search, and profile lifecycle data. `auth-service` will own authentication account lifecycle APIs so user creation/deactivation respects database-per-service boundaries.

## Key Changes
- Add `user-service` models and migration:
  - Support tables: `Institution`, `Department`, and `Batch` with no CRUD APIs yet; T-005 will add management APIs.
  - Profile tables: `UserProfile`, `StudentProfile`, `InstructorProfile`, `AdminProfile`.
  - Future import table: `UserImportJob`.
  - Match `DATABASE_SCHEMA.md` table names, UUID PKs, FKs, status enums, indexes, soft-delete fields, and role-specific profile tables.

- Add auth-service admin account APIs:
  - `POST /api/auth/accounts/`
    - Creates `Account` + `Credential`.
    - Accepts `email`, optional `phone`, `temporary_password`, optional `role_code`, `scope_type`, and `scope_id`.
    - Stores password hash only and sets `must_change_password=true`.
    - Optionally creates the initial RBAC role assignment atomically inside auth-service.
  - `PATCH /api/auth/accounts/<uuid>/`
    - Updates account email/phone/status fields allowed by T-004.
  - `POST /api/auth/accounts/<uuid>/deactivate/`
    - Sets account status to `deactivated`, revokes active refresh tokens, and invalidates existing access tokens through the existing T-002 password-change timestamp path.
  - These endpoints require `profile.manage`; platform-scope account operations require Super Admin.

- Add user-service APIs:
  - `POST /api/users/profiles/`
    - Creates auth account through auth-service, creates the base profile, creates the matching student/instructor/admin profile, and returns the full profile representation.
    - Uses `profile.manage` authorization at `institution` scope when `institution_id` is present, otherwise `platform`.
    - If local profile creation fails after auth account creation, call auth-service deactivate as compensation.
  - `GET /api/users/profiles/`
    - Supports `institution_id`, `q`, `profile_type`, `status`, `department_id`, `batch_id`, `sort`, `page`, and `page_size`.
    - Returns DRF-style paginated response: `count`, `next`, `previous`, `results`.
    - Enforces `profile.view` at institution scope; Super Admin may query platform-wide.
  - `GET /api/users/profiles/<uuid>/`
    - Returns base profile plus role-specific profile data.
  - `PATCH /api/users/profiles/<uuid>/`
    - Updates local profile fields and optional auth account email/phone through auth-service.
  - `POST /api/users/profiles/<uuid>/deactivate/`
    - Sets profile status to `deactivated`, soft-deletes where appropriate, and calls auth-service account deactivation.
  - `POST /api/users/import-jobs/`
    - Future-release placeholder returning `501` with a stable `not_implemented` response; model exists for later T-004/T-005/T-022 expansion.

- Add user-service internals:
  - Serializers for create/update/search/detail responses.
  - Selectors for institution-scoped filtered search.
  - Services for create/update/deactivate orchestration and auth-service HTTP calls.
  - Permission classes for `profile.view` and `profile.manage` using the T-003 remote authorization helper.
  - Include `apps.users.urls` under `/api/users/`.

- Update docs:
  - Document T-004 APIs and profile lifecycle behavior in `docs/DEVELOPMENT.md`.
  - Update `docs/CHANGELOG.md` and `docs/LIVING_DOCUMENT.md`.
  - Mark `T-004.01` through `T-004.08` complete only after verification passes.

## Test Plan
- Auth-service tests:
  - Admin can create an account with temporary password and `must_change_password=true`.
  - Account creation can assign an RBAC role.
  - Unauthorized account creation is denied.
  - Deactivation changes account status and invalidates tokens.
  - Account update changes email/phone without exposing password data.

- User-service tests:
  - Create student, instructor, and admin profiles linked to auth account IDs.
  - Update profile and optional auth account fields.
  - Deactivate profile and auth account together.
  - Search supports pagination, filtering, sorting, and institution scope.
  - Institution-scoped admin cannot access another institution’s profiles.
  - Bulk import placeholder returns `501`.
  - Auth-service failure during create/update/deactivate returns a controlled API error.
  - Local create failure after auth account creation triggers auth deactivation compensation.

- Verification:
  - `auth-service` and `user-service`: `poetry run ruff check .`, `poetry run python manage.py check`, `poetry run python manage.py makemigrations --check --dry-run`, and `poetry run pytest`.
  - Run existing backend service checks if shared auth/permission helper behavior changes.
  - Existing `pnpm dev` stack should be stopped or restarted after migrations because it is currently occupying local ports.

## Assumptions
- Auth-service remains the only service that writes `auth_db`; user-service never writes auth tables directly.
- T-004 creates organization support models only; T-005 will add institution, department, and batch CRUD APIs.
- Temporary passwords are supplied by the admin API caller and are never returned after creation.
- Course-level student/instructor assignment remains for later course/enrollment tasks; T-004 uses institution/platform scope for profile management.
- Bulk import processing is future-release scope; T-004 only adds the model and placeholder endpoint.
