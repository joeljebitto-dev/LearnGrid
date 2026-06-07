# Frontend Architecture

Source: [SRD.pdf](SRD.pdf)

## FE-001 Stack
Service ID: `SVC-011`  
Service name: `frontend-service`  
Database: Not applicable.

The frontend uses React, TypeScript, Tailwind CSS, React Router, TanStack Query, Axios, React Hook Form, and Zod.

## FE-002 Suggested Structure
```text
frontend/src/app
frontend/src/api
frontend/src/components
frontend/src/features/auth
frontend/src/features/courses
frontend/src/features/enrollment
frontend/src/features/assessments
frontend/src/features/dashboard
frontend/src/features/profile
frontend/src/hooks
frontend/src/layouts
frontend/src/routes
frontend/src/stores
frontend/src/types
frontend/src/utils
```

## FE-003 Application Requirements
- Implement route-based code splitting.
- Implement protected routes for authenticated users.
- Implement role-aware navigation and UI rendering.
- Implement separate layouts for student, instructor, and admin portals.
- Use TanStack Query for server-state caching and retry handling.
- Use React Hook Form and Zod for form state and validation.
- Handle loading, error, empty, disabled, optimistic, and retry states.
- Never rely on frontend checks for authorization; backend services remain authoritative.

## FE-004 Portal Requirements
| Portal | Required capabilities | Related specs |
| --- | --- | --- |
| Student | Active courses, lesson viewing, assessments, progress, grades, notifications | [SPEC-010](specs/010-learning-progress-tracking.md), [SPEC-011](specs/011-dashboards-portals.md) |
| Instructor | Course authoring, content upload, assessment authoring, grading, learner progress | [SPEC-006](specs/006-course-catalog-metadata.md), [SPEC-012](specs/012-assessment-authoring.md), [SPEC-015](specs/015-grading-results-audit.md) |
| Admin | User management, course management, enrollment, reports, institution controls | [SPEC-004](specs/004-user-profile-management.md), [SPEC-009](specs/009-enrollment-access-management.md), [SPEC-018](specs/018-search-reporting-analytics.md) |

## FE-005 Related Tasks
See [T-011](tasks/T-011-dashboards-portals.md), [T-001](tasks/T-001-project-setup.md), and [T-024](tasks/T-024-testing-quality.md).
