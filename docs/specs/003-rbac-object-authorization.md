# SPEC-003 RBAC And Object Authorization

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-003](../tasks/T-003-rbac-object-authorization.md)  
Related schema: [auth_db](../DATABASE_SCHEMA.md#auth_db)

## Functional Requirements
- SPEC-003-FR-001 The system shall support role-based access control for Super Admin, Institution Admin, Instructor, Teaching Assistant, Student, and optional Parent or Guardian users.
- SPEC-003-FR-002 The system shall enforce backend authorization for every protected API endpoint.
- SPEC-003-FR-003 The system shall support object-level authorization for courses, enrollments, assessments, submissions, grades, content, and profile records.
- SPEC-003-FR-004 The system shall support platform, institution, course, and assessment authorization scopes.
- SPEC-003-FR-005 Permission changes shall be audit logged.

## Non-Functional Requirements
- SPEC-003-NFR-001 Authorization checks shall not trust frontend-only role rendering.
- SPEC-003-NFR-002 Frequently accessed permissions may be cached in Redis with safe invalidation.
- SPEC-003-NFR-003 Authorization failures shall not leak sensitive object existence.

## Acceptance Criteria
- SPEC-003-AC-001 Super Admin users can perform platform-wide actions.
- SPEC-003-AC-002 Institution Admin users are restricted to their institution scope.
- SPEC-003-AC-003 Instructors and Teaching Assistants can access only assigned courses and permitted workflows.
- SPEC-003-AC-004 Students can access only enrolled courses and their own records.
- SPEC-003-AC-005 Parent or Guardian users can access only limited linked student progress and notifications.

## Implementation Notes
- `auth-service` owns RBAC roles, permissions, assignments, authorization checks, Redis permission cache, and authorization audit logs.
- Other backend services validate access JWTs locally and call `POST /api/auth/authorization/check/` for permission decisions.
- Permission checks use exact scope matching for `platform`, `institution`, `course`, and `assessment` until domain hierarchy models are implemented.
- Permission cache entries use Redis TTL `AUTH_PERMISSION_CACHE_TTL_SECONDS` and fall back to database checks if Redis is unavailable.
