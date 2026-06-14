# T-025 Frontend Feature Completion

Related specs: [SPEC-006](../specs/006-course-catalog-metadata.md), [SPEC-007](../specs/007-course-structure-versioning.md), [SPEC-008](../specs/008-content-upload-storage-access.md), [SPEC-009](../specs/009-enrollment-access-management.md), [SPEC-010](../specs/010-learning-progress-tracking.md), [SPEC-011](../specs/011-dashboards-portals.md), [SPEC-012](../specs/012-assessment-authoring.md), [SPEC-013](../specs/013-quiz-attempts-exams.md), [SPEC-014](../specs/014-assignment-submissions.md), [SPEC-015](../specs/015-grading-results-audit.md), [SPEC-016](../specs/016-certificates.md), [SPEC-017](../specs/017-notifications.md), [SPEC-018](../specs/018-search-reporting-analytics.md), [SPEC-024](../specs/024-testing-quality.md)
Related doc: [FRONTEND_ARCHITECTURE.md](../FRONTEND_ARCHITECTURE.md)

- [ ] T-025.01 Implement course catalog browsing UI with filters, search, pagination, and permission-aware empty states.
- [ ] T-025.02 Implement course detail UI with metadata, modules, lessons, outcomes, prerequisites, and enrollment actions.
- [ ] T-025.03 Implement instructor course builder and course management UI for draft, publish, archive, and delete workflows.
- [ ] T-025.04 Implement module, lesson, and topic authoring UI with ordering, content attachment, validation, and save states.
- [ ] T-025.05 Implement content upload UI for presigned and proxy uploads, upload completion, validation errors, and access links.
- [ ] T-025.06 Implement lesson, video, and content player UI with progress updates and access-denied states.
- [ ] T-025.07 Implement enrollment management UI for individual, batch, cohort, history, and access-grant workflows.
- [ ] T-025.08 Implement student learning-progress UI for lesson, video, assessment, and course completion views.
- [ ] T-025.09 Implement assessment authoring UI for question banks, questions, quizzes, exams, assignments, publish, and close workflows.
- [ ] T-025.10 Implement student quiz, exam, and assignment attempt UI with draft save, submit, auto-submit, and late-submission handling.
- [ ] T-025.11 Implement instructor grading and manual review UI for records, reviews, overrides, publication, and result visibility.
- [ ] T-025.12 Implement certificate viewing, certificate asset linking, revocation visibility, and notification center UI.
- [ ] T-025.13 Implement analytics and reporting UI beyond dashboard summary cards, including search, report generation, and snapshots.
- [ ] T-025.14 Harden frontend loading, error, empty, retry, disabled, no-access, and permission states across every feature route.
- [ ] T-025.15 Validate responsive behavior, keyboard navigation, accessible labels, focus handling, and form error announcements.
- [ ] T-025.16 Expand frontend E2E coverage for major student, instructor, and admin journeys.

Notes:
- Current frontend implementation covers the login, SSO callback, role dashboards, and admin create-user baseline.
- These checklist items remain unchecked until the UI is implemented, tested, and verified against the backend APIs.
- Frontend authorization checks are only presentation controls; backend authorization remains authoritative.
