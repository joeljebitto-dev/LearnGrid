# T-005 Institution, Batch, And Department Management Plan

## Summary
Implement `T-005` in `user-service`. T-004 already created the `Institution`, `Department`, and `Batch` models, so T-005 will add management APIs, serializers, selectors, services, scoped authorization, tests, and documentation. No cohort CRUD is added because the T-005 task and `user_db` schema only define institutions, departments, and batches.

## Key Changes
- Add organization management APIs under `/api/users/`:
  - `GET /institutions/`, `POST /institutions/`, `GET/PATCH/DELETE /institutions/<uuid>/`
  - `GET /departments/`, `POST /departments/`, `GET/PATCH/DELETE /departments/<uuid>/`
  - `GET /batches/`, `POST /batches/`, `GET/PATCH/DELETE /batches/<uuid>/`
- Use existing `Institution`, `Department`, and `Batch` models; do not add new model fields unless Django migration checks reveal drift.
- Add serializers for create, update, list/detail, and search:
  - Institution fields: `id`, `name`, `code`, `status`, `settings`, timestamps, `deleted_at`.
  - Department fields: `id`, `institution_id`, `name`, `code`, `status`, timestamps, `deleted_at`.
  - Batch fields: `id`, `institution_id`, `department_id`, `name`, `start_date`, `end_date`, `status`, timestamps, `deleted_at`.
- Normalize organization `code` values by trimming and uppercasing on create/update. Soft-deleted codes remain reserved because current database constraints are unique.
- Add selectors for filtered, paginated search:
  - Institutions: `q`, `status`, `sort`, `page`, `page_size`.
  - Departments: `institution_id`, `q`, `status`, `sort`, `page`, `page_size`.
  - Batches: `institution_id`, `department_id`, `q`, `status`, `sort`, `page`, `page_size`.
- Add service functions for create/update/soft-delete:
  - `DELETE` sets `deleted_at=now()` and status `archived`, then returns the serialized resource.
  - Deleted records are excluded from list/detail/update/delete lookups.
  - Batch create/update validates that `department_id`, when supplied, belongs to the selected `institution_id`.
  - Batch date validation rejects `end_date` earlier than `start_date`.

## Authorization
- Institution endpoints require `institution.manage` at platform scope, so only Super Admin can create, update, list, read, or delete institutions.
- Department and batch create/update/delete/detail require `institution.manage` at the target institution scope.
- Department and batch list behavior:
  - If `institution_id` is provided, authorize `institution.manage` at that institution scope.
  - If `institution_id` is omitted, authorize `institution.manage` at platform scope, limiting platform-wide listing to Super Admin.
- Authorization uses the existing T-003 remote authorization helper and denies by default if auth-service is unreachable or rejects the check.

## Documentation Updates
- Update `docs/DEVELOPMENT.md` with T-005 endpoint contracts, filters, auth rules, and soft-delete behavior.
- Update `docs/CHANGELOG.md` and `docs/LIVING_DOCUMENT.md`.
- Add implemented design docs:
  - `docs/db-design/DBD-005-institution-batch-department-management.md`
  - `docs/api-design/API-005-institution-batch-department-management.md`
  - Update both design folder READMEs.
- Mark `T-005.01` through `T-005.08` complete only after verification passes.

## Test Plan
- User-service API tests:
  - Super Admin can create, list, read, update, and soft-delete institutions.
  - Non-Super Admin cannot manage institutions.
  - Institution Admin can manage departments inside their institution.
  - Institution Admin cannot read, update, delete, or list another institution’s departments.
  - Institution Admin can manage batches inside their institution.
  - Batch creation/update rejects a department from another institution.
  - Search supports pagination, filtering, sorting, and excludes soft-deleted records.
  - Soft delete preserves records and historical foreign key relationships.
  - Auth-service denial or network failure denies access.
- Verification commands for `user-service`:
  - `poetry run ruff check .`
  - `poetry run python manage.py check`
  - `poetry run python manage.py makemigrations --check --dry-run`
  - `poetry run pytest`
- Existing `pnpm dev` stack should be restarted after code changes so user-service loads new routes.

## Assumptions
- T-005 does not add cohort CRUD; cohort enrollment remains future enrollment-service scope.
- Existing T-004 models and indexes satisfy the database schema for T-005.
- `institution.manage` is the correct RBAC permission for institutions, departments, and batches because it is already seeded for Super Admin and Institution Admin roles.
- No code changes should be made to auth-service for T-005.
