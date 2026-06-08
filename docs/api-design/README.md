# API Design Documents

These documents capture implemented API design decisions for LearnGrid LMS.
They summarize implemented contracts and link back to task, spec, and architecture sources.

## Numbering
API design documents use stable IDs:

- `API-001` for project setup and service health/dev stack interfaces.
- `API-002` onward for implemented feature API designs.

## Implemented Designs
| ID | Design | Related task | Related spec |
| --- | --- | --- | --- |
| [API-001](API-001-service-health-and-dev-stack.md) | Service Health And Dev Stack | [T-001](../tasks/T-001-project-setup.md) | [SPEC-001](../specs/001-authentication-lifecycle.md) |
| [API-002](API-002-token-session-security.md) | Token Session Security | [T-002](../tasks/T-002-token-session-security.md) | [SPEC-002](../specs/002-token-session-security.md) |
| [API-003](API-003-rbac-authorization.md) | RBAC Authorization | [T-003](../tasks/T-003-rbac-object-authorization.md) | [SPEC-003](../specs/003-rbac-object-authorization.md) |
| [API-004](API-004-user-profile-management.md) | User Profile Management | [T-004](../tasks/T-004-user-profile-management.md) | [SPEC-004](../specs/004-user-profile-management.md) |
| [API-005](API-005-institution-batch-department-management.md) | Institution, Batch, And Department Management | [T-005](../tasks/T-005-institution-batch-department-management.md) | [SPEC-005](../specs/005-institution-batch-department-management.md) |
| [API-006](API-006-course-catalog-metadata.md) | Course Catalog And Metadata | [T-006](../tasks/T-006-course-catalog-metadata.md) | [SPEC-006](../specs/006-course-catalog-metadata.md) |
| [API-007](API-007-course-structure-versioning.md) | Course Structure And Versioning | [T-007](../tasks/T-007-course-structure-versioning.md) | [SPEC-007](../specs/007-course-structure-versioning.md) |
| [API-008](API-008-content-upload-storage-access.md) | Content Upload, Storage, And Access | [T-008](../tasks/T-008-content-upload-storage-access.md) | [SPEC-008](../specs/008-content-upload-storage-access.md) |
| [API-009](API-009-enrollment-access-management.md) | Enrollment And Access Management | [T-009](../tasks/T-009-enrollment-access-management.md) | [SPEC-009](../specs/009-enrollment-access-management.md) |
| [API-010](API-010-learning-progress-tracking.md) | Learning Progress Tracking | [T-010](../tasks/T-010-learning-progress-tracking.md) | [SPEC-010](../specs/010-learning-progress-tracking.md) |
| [API-011](API-011-dashboards-portals.md) | Dashboards And Portals | [T-011](../tasks/T-011-dashboards-portals.md) | [SPEC-011](../specs/011-dashboards-portals.md) |
| [API-012](API-012-assessment-authoring.md) | Assessment Authoring | [T-012](../tasks/T-012-assessment-authoring.md) | [SPEC-012](../specs/012-assessment-authoring.md) |
| [API-013](API-013-quiz-attempts-exams.md) | Quiz Attempts And Exams | [T-013](../tasks/T-013-quiz-attempts-exams.md) | [SPEC-013](../specs/013-quiz-attempts-exams.md) |

## Rules
- Add one `API-###-<topic>.md` file after a task with API design is implemented.
- Link every design file to its related task, spec, and relevant development or architecture docs.
- Capture endpoint paths, request and response shapes, auth requirements, failure behavior, and tests.
- Do not document future task APIs as implemented until their task checklist is complete.
