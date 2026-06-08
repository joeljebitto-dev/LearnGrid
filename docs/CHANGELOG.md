# Changelog

Source: [SRD.pdf](SRD.pdf)

## 2026-06-04
- CHG-001 Created initial documentation plan for LearnGrid LMS from `SRD.pdf`.
- CHG-002 Added stable numbering model for specs, requirements, tasks, database tables, and open decisions.
- CHG-003 Included all SRD future-release items in the documented scope.
- CHG-004 Preserved SRD open decisions without choosing final options.
- CHG-005 Implemented `T-001 Project Setup` with frontend, backend service scaffolds, local infrastructure baseline, CI, development docs, lockfiles, and health checks.
- CHG-006 Implemented `T-002 Token And Session Security` in auth-service with JWT access/refresh tokens, refresh rotation, logout revocation, Redis/DB blacklist checks, token invalidation, API tests, and token lifetime documentation.
- CHG-007 Implemented `T-003 RBAC And Object Authorization` with auth-service RBAC tables, seeded role and permission catalog, scoped assignments, authorization APIs, Redis permission cache, audit logs, and non-auth service authorization helpers.

## 2026-06-06
- CHG-008 Implemented `T-004 User And Profile Management` with auth-service account lifecycle APIs, user-service institution/profile models, profile create/update/deactivate/search APIs, bulk import placeholder, migrations, and API tests.

## 2026-06-07
- CHG-009 Added implemented database design and API design documentation folders with T-001 through T-004 design records.
- CHG-010 Implemented `T-005 Institution, Batch, And Department Management` with user-service organization APIs, scoped authorization, soft-delete behavior, tests, and design documentation.
- CHG-011 Added overall `DB_STRUCTURE.md` and `API_STRUCTURE.md` aggregate documentation for schema tables/fields and implemented API contracts.
- CHG-012 Implemented `T-006 Course Catalog And Metadata` with course-service catalog models, metadata APIs, lifecycle workflows, Redis catalog cache, local structured course events, tests, and design documentation.
- CHG-013 Implemented `T-007 Course Structure And Versioning` with course-service modules, lessons, topics, reorder APIs, lesson publishing events, revision snapshots, tests, and design documentation.
- CHG-014 Implemented the `T-008` content metadata/access baseline with upload validation, signed access, content permissions, versions, local content events, tests, and provider selection later resolved in `CHG-017`.
- CHG-015 Implemented `T-009 Enrollment And Access Management` with enrollment state, batch/cohort jobs, history, access grants, access checks, local enrollment events, tests, and design documentation.
- CHG-016 Implemented `T-010 Learning Progress Tracking` with lesson/video/assessment/course progress, idempotent event ingestion, local progress events, tests, and design documentation.
- CHG-017 Resolved `OD-002` by selecting MinIO, added local MinIO infrastructure, completed `T-008.03`, and implemented presigned/proxy upload plus MinIO-backed signed download behavior in content-service.
- CHG-018 Implemented `T-011 Dashboards And Portals` with role-aware protected frontend routes, session/profile context, analytics dashboard/report APIs, analytics tables, Selenium smoke scaffolding, tests, and design documentation while keeping `OD-005` open.
- CHG-019 Implemented `T-012 Assessment Authoring` and `T-013 Quiz Attempts And Exams` with assessment-service authoring APIs, quiz/exam attempts, durable answers, auto-submit behavior, local assessment events, tests, and design documentation.
- CHG-020 Implemented `T-014 Assignment Submissions` and `T-015 Grading, Results, And Audit` with assessment-service assignment submissions, grading-source APIs, grading-service rules/records/reviews/history/publication, local grade events, tests, and design documentation.
- CHG-021 Implemented `T-016 Certificates` with grading-service certificate eligibility, auto-issued certificates, optional asset linking, revocation handling, `CertificateEligible` events, tests, and design documentation.
- CHG-022 Implemented `T-017 Notifications` with notification-service templates, in-app records, preferences, delivery attempts, event ingestion for enrollment/deadline/grade/course-completion events, tests, and design documentation.
