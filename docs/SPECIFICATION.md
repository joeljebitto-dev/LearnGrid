# LearnGrid LMS Specification Index

Source: [SRD.pdf](SRD.pdf)

## Numbering
- Specs use `SPEC-001`.
- Functional requirements use `SPEC-001-FR-001`.
- Non-functional requirements use `SPEC-001-NFR-001`.
- Acceptance criteria use `SPEC-001-AC-001`.
- Database tables use `DB-AUTH-001`.
- Tasks use `T-001`.

## Spec Index
| Spec | Title | Related task | Related schema |
| --- | --- | --- | --- |
| [SPEC-001](specs/001-authentication-lifecycle.md) | Authentication Lifecycle | [T-001](tasks/T-001-project-setup.md) | [Auth tables](DATABASE_SCHEMA.md#auth_db) |
| [SPEC-002](specs/002-token-session-security.md) | Token And Session Security | [T-002](tasks/T-002-token-session-security.md) | [Auth tables](DATABASE_SCHEMA.md#auth_db) |
| [SPEC-003](specs/003-rbac-object-authorization.md) | RBAC And Object Authorization | [T-003](tasks/T-003-rbac-object-authorization.md) | [Auth tables](DATABASE_SCHEMA.md#auth_db) |
| [SPEC-004](specs/004-user-profile-management.md) | User And Profile Management | [T-004](tasks/T-004-user-profile-management.md) | [User tables](DATABASE_SCHEMA.md#user_db) |
| [SPEC-005](specs/005-institution-batch-department-management.md) | Institution, Batch, And Department Management | [T-005](tasks/T-005-institution-batch-department-management.md) | [User tables](DATABASE_SCHEMA.md#user_db) |
| [SPEC-006](specs/006-course-catalog-metadata.md) | Course Catalog And Metadata | [T-006](tasks/T-006-course-catalog-metadata.md) | [Course tables](DATABASE_SCHEMA.md#course_db) |
| [SPEC-007](specs/007-course-structure-versioning.md) | Course Structure And Versioning | [T-007](tasks/T-007-course-structure-versioning.md) | [Course tables](DATABASE_SCHEMA.md#course_db) |
| [SPEC-008](specs/008-content-upload-storage-access.md) | Content Upload, Storage, And Access | [T-008](tasks/T-008-content-upload-storage-access.md) | [Content tables](DATABASE_SCHEMA.md#content_db) |
| [SPEC-009](specs/009-enrollment-access-management.md) | Enrollment And Access Management | [T-009](tasks/T-009-enrollment-access-management.md) | [Enrollment tables](DATABASE_SCHEMA.md#enrollment_db) |
| [SPEC-010](specs/010-learning-progress-tracking.md) | Learning Progress Tracking | [T-010](tasks/T-010-learning-progress-tracking.md) | [Progress tables](DATABASE_SCHEMA.md#progress_db) |
| [SPEC-011](specs/011-dashboards-portals.md) | Dashboards And Portals | [T-011](tasks/T-011-dashboards-portals.md) | [Analytics tables](DATABASE_SCHEMA.md#analytics_db) |
| [SPEC-012](specs/012-assessment-authoring.md) | Assessment Authoring | [T-012](tasks/T-012-assessment-authoring.md) | [Assessment tables](DATABASE_SCHEMA.md#assessment_db) |
| [SPEC-013](specs/013-quiz-attempts-exams.md) | Quiz Attempts And Exams | [T-013](tasks/T-013-quiz-attempts-exams.md) | [Assessment tables](DATABASE_SCHEMA.md#assessment_db) |
| [SPEC-014](specs/014-assignment-submissions.md) | Assignment Submissions | [T-014](tasks/T-014-assignment-submissions.md) | [Assessment tables](DATABASE_SCHEMA.md#assessment_db) |
| [SPEC-015](specs/015-grading-results-audit.md) | Grading, Results, And Audit | [T-015](tasks/T-015-grading-results-audit.md) | [Grading tables](DATABASE_SCHEMA.md#grading_db) |
| [SPEC-016](specs/016-certificates.md) | Certificates | [T-016](tasks/T-016-certificates.md) | [Grading tables](DATABASE_SCHEMA.md#grading_db) |
| [SPEC-017](specs/017-notifications.md) | Notifications | [T-017](tasks/T-017-notifications.md) | [Notification tables](DATABASE_SCHEMA.md#notification_db) |
| [SPEC-018](specs/018-search-reporting-analytics.md) | Search, Reporting, And Analytics | [T-018](tasks/T-018-search-reporting-analytics.md) | [Analytics tables](DATABASE_SCHEMA.md#analytics_db) |
| [SPEC-019](specs/019-api-gateway.md) | API Gateway | [T-019](tasks/T-019-api-gateway.md) | Not applicable |
| [SPEC-020](specs/020-kafka-eventing.md) | Kafka Eventing | [T-020](tasks/T-020-kafka-eventing.md) | [Analytics events](DATABASE_SCHEMA.md#analytics_db) |
| [SPEC-021](specs/021-redis-architecture.md) | Redis Architecture | [T-021](tasks/T-021-redis-architecture.md) | Not applicable |
| [SPEC-022](specs/022-security.md) | Security | [T-022](tasks/T-022-security.md) | All service schemas |
| [SPEC-023](specs/023-ci-cd-deployment-observability.md) | CI/CD, Deployment, And Observability | [T-023](tasks/T-023-ci-cd-deployment-observability.md) | Not applicable |
| [SPEC-024](specs/024-testing-quality.md) | Testing And Quality | [T-024](tasks/T-024-testing-quality.md) | All service schemas |
