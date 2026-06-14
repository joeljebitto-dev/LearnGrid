# T-025 Frontend Feature Completion Implementation Plan

## Summary
Implement `T-025` as a full frontend expansion on top of the existing login, role dashboards, SSO callback, and admin create-user baseline. The work stays frontend-focused: use the backend APIs already documented in `docs/API_STRUCTURE.md`, do not add new backend contracts, and show controlled unavailable/error states if an expected backend capability is missing.

## Key Changes
- Refactor the frontend into feature modules so `App.tsx` becomes route composition only:
  - `features/auth`, `layout`, `courses`, `content`, `enrollment`, `progress`, `assessments`, `grading`, `certificates`, `notifications`, `analytics`, and `shared`.
  - Extract reusable protected-route guards, portal layout, navigation, loading/error/empty states, form fields, data tables, pagination, and API error handling.

- Add frontend API clients using existing Axios bearer-token behavior:
  - Courses/catalog/detail/builder metadata.
  - Content asset upload/access.
  - Enrollment and access management.
  - Progress/course learning state.
  - Assessment authoring, quiz attempts, and assignment submissions.
  - Grading/manual reviews/published results/certificates.
  - Notifications and analytics/reporting.
  - Use `docs/API_STRUCTURE.md` as the contract source.

- Add role-specific route groups under the existing dashboard shell:
  - Student: catalog browse/detail, learning player, progress, assessment attempts, assignment submission, certificates, notifications.
  - Instructor: course builder, module/lesson/topic authoring, content upload, assessment authoring, grading/manual reviews, reports.
  - Admin: keep dashboard and create-user, then add enrollment management, reporting, notification oversight, and platform/institution views where APIs exist.

- Implement the T-025 checklist areas end to end:
  - `T-025.01` to `T-025.03`: catalog, course detail, and course builder UI.
  - `T-025.04` to `T-025.06`: structure authoring, content upload, and lesson/content player.
  - `T-025.07` to `T-025.08`: enrollment and progress UI.
  - `T-025.09` to `T-025.11`: assessment authoring, student attempts, grading/manual review.
  - `T-025.12` to `T-025.13`: certificates, notifications, analytics/reporting.
  - `T-025.14` to `T-025.16`: state hardening, accessibility/responsive behavior, and E2E coverage.

- Keep frontend authorization role-aware but not security-authoritative:
  - Hide irrelevant navigation by role.
  - Preserve backend authorization as the source of truth.
  - Render `No Access` or controlled API error states for denied requests.

- Update docs only where needed:
  - Mark `docs/tasks/T-025-frontend-feature-completion.md` items complete after verification passes.
  - Add concise frontend route/run notes to development docs if the current docs do not already cover the new routes.
  - Do not change backend task statuses.

## Public Interfaces
- No backend API changes.
- No new environment variables required.
- New frontend routes live under existing dashboard paths, for example:
  - `/dashboard/student/courses`
  - `/dashboard/student/courses/:courseId`
  - `/dashboard/student/courses/:courseId/learn`
  - `/dashboard/student/assessments/:assessmentId/attempt`
  - `/dashboard/student/assignments/:assignmentId/submit`
  - `/dashboard/student/certificates`
  - `/dashboard/instructor/courses`
  - `/dashboard/instructor/courses/:courseId/builder`
  - `/dashboard/instructor/assessments`
  - `/dashboard/instructor/grading`
  - `/dashboard/admin/enrollments`
  - `/dashboard/admin/reports`
  - `/dashboard/admin/notifications`

## Test Plan
- Add Vitest/React Testing Library coverage for:
  - role-based navigation and route access;
  - catalog/detail/builder rendering;
  - content upload form behavior;
  - enrollment/progress screens;
  - assessment attempt and assignment submission flows;
  - grading/manual review forms;
  - certificates, notifications, and reporting states;
  - loading, empty, retry, denied, and API failure states.

- Add or extend Selenium E2E smoke coverage for:
  - login to each portal type;
  - student course learning journey;
  - instructor authoring/grading journey;
  - admin management/reporting journey.

- Verification commands:
  - `pnpm -C frontend lint`
  - `pnpm -C frontend typecheck`
  - `pnpm -C frontend test`
  - `pnpm -C frontend build`
  - `python -m pytest tests/e2e` when a browser/driver is available.

## Assumptions
- T-025 is frontend implementation only.
- Existing backend APIs from T-006 through T-020 are the contract source.
- Missing backend parity found during frontend work is documented for `T-026`, not solved inside `T-025`.
- Current dependencies remain: React, Vite, TypeScript, Tailwind, React Router, TanStack Query, Axios, React Hook Form, Zod, and Vitest.
