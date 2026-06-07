# DBD-005 Institution, Batch, And Department Management

Related task: [T-005 Institution, Batch, And Department Management](../tasks/T-005-institution-batch-department-management.md)  
Related spec: [SPEC-005 Institution, Batch, And Department Management](../specs/005-institution-batch-department-management.md)  
Canonical schema: [user_db](../DATABASE_SCHEMA.md#user_db)

## Design Summary
T-005 operationalizes the organization support tables created in T-004. `user-service` owns
institution, department, and batch records and exposes management APIs for them. No cohort table
or cohort CRUD was added because the implemented `user_db` schema for T-005 defines only
institutions, departments, and batches.

## Implemented Tables
| Table ID | Table | Purpose |
| --- | --- | --- |
| `DB-USER-001` | `institutions` | Institution records managed by Super Admin users |
| `DB-USER-002` | `departments` | Institution-scoped departments managed by Institution Admin users |
| `DB-USER-003` | `batches` | Institution-scoped batches, optionally linked to departments |

## Relationships And Constraints
- `departments.institution_id` and `batches.institution_id` are in-service foreign keys.
- `batches.department_id` is optional and must reference a department in the same institution.
- Institution `code` is globally unique.
- Department `code` is unique per institution.
- Organization codes are normalized to uppercase on create and update.

## Indexes And Search
- Institution status, department institution/status, batch institution/status, and batch department indexes support T-005 filters.
- Search endpoints filter out soft-deleted records.
- List endpoints support DRF pagination and sort by name, code, status, created time, or updated time.

## Soft Delete
`DELETE` operations set `deleted_at` and archive the record status. Soft-deleted records are excluded
from list/detail/update/delete lookups, while historical foreign key relationships remain intact.

## Verification
T-005 tests cover Super Admin institution management, Institution Admin department and batch
management, cross-institution denial, batch department validation, search filtering, pagination,
soft-delete preservation, and remote authorization denial.
