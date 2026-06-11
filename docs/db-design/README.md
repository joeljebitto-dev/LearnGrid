# Database Design Documents

These documents capture implemented database design decisions for LearnGrid LMS.
The canonical full table and field reference remains [DATABASE_SCHEMA.md](../DATABASE_SCHEMA.md).

## Numbering
Database design documents use stable IDs:

- `DBD-001` for project setup and service database ownership.
- `DBD-002` onward for implemented feature database designs.

## Implemented Designs
| ID | Design | Related task | Related spec |
| --- | --- | --- | --- |
| [DBD-001](DBD-001-service-databases.md) | Service Databases | [T-001](../tasks/T-001-project-setup.md) | [SPEC-001](../specs/001-authentication-lifecycle.md) |
| [DBD-002](DBD-002-auth-token-session.md) | Auth Token And Session | [T-002](../tasks/T-002-token-session-security.md) | [SPEC-002](../specs/002-token-session-security.md) |
| [DBD-003](DBD-003-rbac-authorization.md) | RBAC Authorization | [T-003](../tasks/T-003-rbac-object-authorization.md) | [SPEC-003](../specs/003-rbac-object-authorization.md) |
| [DBD-004](DBD-004-user-profile-management.md) | User Profile Management | [T-004](../tasks/T-004-user-profile-management.md) | [SPEC-004](../specs/004-user-profile-management.md) |
| [DBD-005](DBD-005-institution-batch-department-management.md) | Institution, Batch, And Department Management | [T-005](../tasks/T-005-institution-batch-department-management.md) | [SPEC-005](../specs/005-institution-batch-department-management.md) |
| [DBD-006](DBD-006-course-catalog-metadata.md) | Course Catalog And Metadata | [T-006](../tasks/T-006-course-catalog-metadata.md) | [SPEC-006](../specs/006-course-catalog-metadata.md) |
| [DBD-007](DBD-007-course-structure-versioning.md) | Course Structure And Versioning | [T-007](../tasks/T-007-course-structure-versioning.md) | [SPEC-007](../specs/007-course-structure-versioning.md) |
| [DBD-008](DBD-008-content-upload-storage-access.md) | Content Upload, Storage, And Access | [T-008](../tasks/T-008-content-upload-storage-access.md) | [SPEC-008](../specs/008-content-upload-storage-access.md) |
| [DBD-009](DBD-009-enrollment-access-management.md) | Enrollment And Access Management | [T-009](../tasks/T-009-enrollment-access-management.md) | [SPEC-009](../specs/009-enrollment-access-management.md) |
| [DBD-010](DBD-010-learning-progress-tracking.md) | Learning Progress Tracking | [T-010](../tasks/T-010-learning-progress-tracking.md) | [SPEC-010](../specs/010-learning-progress-tracking.md) |
| [DBD-011](DBD-011-dashboards-portals.md) | Dashboards And Portals | [T-011](../tasks/T-011-dashboards-portals.md) | [SPEC-011](../specs/011-dashboards-portals.md) |
| [DBD-012](DBD-012-assessment-authoring.md) | Assessment Authoring | [T-012](../tasks/T-012-assessment-authoring.md) | [SPEC-012](../specs/012-assessment-authoring.md) |
| [DBD-013](DBD-013-quiz-attempts-exams.md) | Quiz Attempts And Exams | [T-013](../tasks/T-013-quiz-attempts-exams.md) | [SPEC-013](../specs/013-quiz-attempts-exams.md) |
| [DBD-014](DBD-014-assignment-submissions.md) | Assignment Submissions | [T-014](../tasks/T-014-assignment-submissions.md) | [SPEC-014](../specs/014-assignment-submissions.md) |
| [DBD-015](DBD-015-grading-results-audit.md) | Grading, Results, And Audit | [T-015](../tasks/T-015-grading-results-audit.md) | [SPEC-015](../specs/015-grading-results-audit.md) |
| [DBD-016](DBD-016-certificates.md) | Certificates | [T-016](../tasks/T-016-certificates.md) | [SPEC-016](../specs/016-certificates.md) |
| [DBD-017](DBD-017-notifications.md) | Notifications | [T-017](../tasks/T-017-notifications.md) | [SPEC-017](../specs/017-notifications.md) |
| [DBD-018](DBD-018-search-reporting-analytics.md) | Search, Reporting, And Analytics | [T-018](../tasks/T-018-search-reporting-analytics.md) | [SPEC-018](../specs/018-search-reporting-analytics.md) |

## Rules
- Keep [DATABASE_SCHEMA.md](../DATABASE_SCHEMA.md) as the field-level source of truth.
- Add one `DBD-###-<topic>.md` file after a task with database design is implemented.
- Link every design file to its related task, spec, and schema section.
- Do not add future task designs as implemented until their task checklist is complete.
