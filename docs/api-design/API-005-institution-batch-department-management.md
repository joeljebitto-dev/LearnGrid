# API-005 Institution, Batch, And Department Management

Related task: [T-005 Institution, Batch, And Department Management](../tasks/T-005-institution-batch-department-management.md)  
Related spec: [SPEC-005 Institution, Batch, And Department Management](../specs/005-institution-batch-department-management.md)  
Related database design: [DBD-005](../db-design/DBD-005-institution-batch-department-management.md)

## Design Summary
T-005 adds organization management APIs to `user-service`. Institution endpoints are platform
management APIs. Department and batch endpoints are institution-scoped APIs.

## Endpoints
| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/users/institutions/` | `institution.manage` platform | Search institutions |
| `POST` | `/api/users/institutions/` | `institution.manage` platform | Create institution |
| `GET` | `/api/users/institutions/<uuid>/` | `institution.manage` platform | Read institution |
| `PATCH` | `/api/users/institutions/<uuid>/` | `institution.manage` platform | Update institution |
| `DELETE` | `/api/users/institutions/<uuid>/` | `institution.manage` platform | Archive institution |
| `GET` | `/api/users/departments/` | `institution.manage` scoped | Search departments |
| `POST` | `/api/users/departments/` | `institution.manage` scoped | Create department |
| `GET` | `/api/users/departments/<uuid>/` | `institution.manage` scoped | Read department |
| `PATCH` | `/api/users/departments/<uuid>/` | `institution.manage` scoped | Update department |
| `DELETE` | `/api/users/departments/<uuid>/` | `institution.manage` scoped | Archive department |
| `GET` | `/api/users/batches/` | `institution.manage` scoped | Search batches |
| `POST` | `/api/users/batches/` | `institution.manage` scoped | Create batch |
| `GET` | `/api/users/batches/<uuid>/` | `institution.manage` scoped | Read batch |
| `PATCH` | `/api/users/batches/<uuid>/` | `institution.manage` scoped | Update batch |
| `DELETE` | `/api/users/batches/<uuid>/` | `institution.manage` scoped | Archive batch |

## Request And Response Behavior
- Institution create/update accepts `name`, `code`, `status`, and `settings`.
- Department create accepts `institution_id`, `name`, `code`, and `status`; update accepts `name`, `code`, and `status`.
- Batch create accepts `institution_id`, optional `department_id`, `name`, `start_date`, `end_date`, and `status`; update accepts optional `department_id`, `name`, dates, and `status`.
- Search responses use DRF pagination: `count`, `next`, `previous`, and `results`.
- `DELETE` returns the archived resource instead of an empty response.

## Auth And Failure Behavior
- Institution endpoints require platform-scope `institution.manage`.
- Department and batch detail/update/delete require `institution.manage` at the resource institution.
- Department and batch list endpoints use institution scope when `institution_id` is provided; otherwise platform scope is required.
- Batch create/update rejects departments from another institution.
- Batch create/update rejects `end_date` earlier than `start_date`.
- Authorization denial or auth-service failure returns access denial through the existing T-003 helper.

## Verification
T-005 tests cover Super Admin institution CRUD, Institution Admin department and batch CRUD,
cross-institution denial, search filters, pagination, sorting, soft-delete exclusion, relationship
preservation after soft delete, invalid batch department references, invalid batch dates, and remote
authorization denial.
