# T-003 RBAC And Object Authorization

Related spec: [SPEC-003](../specs/003-rbac-object-authorization.md)  
Related schema: [auth_db](../DATABASE_SCHEMA.md#auth_db)

- [x] T-003.01 Seed system roles for Super Admin, Institution Admin, Instructor, Teaching Assistant, Student, and Parent or Guardian.
- [x] T-003.02 Implement permission catalog and role-permission assignments.
- [x] T-003.03 Implement role assignment scopes for platform, institution, course, and assessment.
- [x] T-003.04 Implement backend permission classes for protected APIs.
- [x] T-003.05 Implement object-level authorization helpers.
- [x] T-003.06 Add Redis permission cache with invalidation after role changes.
- [x] T-003.07 Add audit logs for permission and role assignment changes.
- [x] T-003.08 Add negative-path tests for unauthorized object access.

## Verification
- `auth-service`: `poetry run ruff check .`, `poetry run python manage.py check`, `poetry run python manage.py makemigrations --check --dry-run`, and `poetry run pytest`.
- Non-auth backend services: same verification commands passed for `user-service`, `course-service`, `content-service`, `enrollment-service`, `progress-service`, `assessment-service`, `grading-service`, `notification-service`, and `analytics-service`.
