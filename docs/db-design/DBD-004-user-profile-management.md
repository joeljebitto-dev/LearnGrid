# DBD-004 User Profile Management

Related task: [T-004 User And Profile Management](../tasks/T-004-user-profile-management.md)  
Related spec: [SPEC-004 User Profile Management](../specs/004-user-profile-management.md)  
Canonical schema: [user_db](../DATABASE_SCHEMA.md#user_db)

## Design Summary
T-004 implemented the first `user-service` domain model set. `user-service` owns profile, organization support, role-specific profile, and import job records in `user_db`. `auth_account_id` is a cross-service UUID reference to `auth_db.accounts.id`; user-service never writes auth tables directly.

## Implemented Tables
| Table ID | Table | Purpose |
| --- | --- | --- |
| `DB-USER-001` | `institutions` | Institution support data; management APIs implemented by T-005 |
| `DB-USER-002` | `departments` | Department support data scoped to institution |
| `DB-USER-003` | `batches` | Batch support data scoped to institution and optionally department |
| `DB-USER-004` | `user_profiles` | Base profile linked to an auth account UUID |
| `DB-USER-005` | `student_profiles` | Student-specific profile attributes |
| `DB-USER-006` | `instructor_profiles` | Instructor-specific profile attributes |
| `DB-USER-007` | `admin_profiles` | Admin-specific profile attributes |
| `DB-USER-008` | `user_import_jobs` | Future bulk import tracking; processing deferred |

## Relationships
- `departments.institution_id`, `batches.institution_id`, and `user_profiles.institution_id` are in-service foreign keys.
- Role-specific profile tables are one-to-one extensions of `user_profiles`.
- `user_profiles.auth_account_id` is unique and references auth-service by UUID only.
- `user_import_jobs.source_file_asset_id` is a cross-service UUID reference to future content assets.

## Status And Soft Delete
- `institutions`, `departments`, `batches`, and `user_profiles` include status fields and `deleted_at` for soft-delete behavior.
- Profile deactivation sets `user_profiles.status = 'deactivated'` and `deleted_at`.
- Auth account deactivation is coordinated through auth-service APIs.

## Indexes And Search
- Institution/status indexes support scoped profile and organization filtering.
- Name indexes support profile search by first name and last name.
- Batch and department indexes support student, instructor, and admin filtering.

## Verification
T-004 tests cover creating student, instructor, and admin profiles, updating profile/auth fields, deactivation with auth-service coordination, paginated search, institution-scoped access denial, import placeholder behavior, auth-service failure handling, and compensation after local create failure.
