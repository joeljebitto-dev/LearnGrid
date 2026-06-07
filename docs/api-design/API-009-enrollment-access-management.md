# API-009 Enrollment And Access Management

Related task: [T-009](../tasks/T-009-enrollment-access-management.md)  
Related spec: [SPEC-009](../specs/009-enrollment-access-management.md)  
Related database design: [DBD-009](../db-design/DBD-009-enrollment-access-management.md)

## API-009-001 Endpoints
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/enrollments/` | Search enrollments | `enrollment.view` |
| `POST` | `/api/enrollments/` | Create individual enrollment | `enrollment.manage` |
| `GET` | `/api/enrollments/<uuid>/` | Read one enrollment | `enrollment.view` |
| `POST` | `/api/enrollments/<uuid>/transition/` | Change enrollment status | `enrollment.manage` |
| `GET` | `/api/enrollments/<uuid>/history/` | Read enrollment history | `enrollment.view` |
| `GET` | `/api/enrollments/access/check/` | Check student course access | `enrollment.view` |
| `GET/POST` | `/api/enrollments/batch-enrollments/` | List or create batch jobs | `enrollment.view/manage` |
| `GET/POST` | `/api/enrollments/cohort-enrollments/` | List or create cohort jobs | `enrollment.view/manage` |

## API-009-002 Notes
Enrollment creates and jobs accept cross-service UUIDs. Batch/cohort job payloads include `student_profile_ids` so local development can create concrete enrollment records before a future cohort membership service exists.
