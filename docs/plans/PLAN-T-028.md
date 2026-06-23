# Instructor Course Workspace, Breadcrumbs, And Admin Course Add People

## Summary
Add a course workspace for instructors, introduce breadcrumbs across instructor pages, and extend admin Courses with add-only student/instructor assignment UI. Use existing enrollment and RBAC APIs; no database migrations or backend schema changes.

## Key Changes
- Instructor course flow:
  - Change `/dashboard/instructor/courses` **Open** links to `/dashboard/instructor/courses/:courseId`.
  - Add `InstructorCourseWorkspacePage` for `/dashboard/instructor/courses/:courseId`.
  - Show a course-local left menu inside the page content with:
    - `Overview` → `/dashboard/instructor/courses/:courseId`
    - `Builder` → `/dashboard/instructor/courses/:courseId/builder`
  - Keep the existing builder route, but render it inside the same course workspace shell/menu.
  - Reuse the existing assigned-course guard for both overview and builder; unassigned courses must show `Course access required` and avoid loading course/structure APIs.

- Instructor breadcrumbs:
  - Add `PageHeader.breadcrumbs` to all instructor portal pages.
  - Use these breadcrumb shapes:
    - Dashboard: `Instructor`
    - Courses: `Instructor > Courses`
    - Course overview: `Instructor > Courses > {Course title}`
    - Builder: `Instructor > Courses > {Course title} > Builder`
    - Content, Assessments, Grading, Reports, Notifications: `Instructor > {Page}`
  - Keep all existing routes and portal nav behavior unchanged.

- Admin Courses add people UI:
  - Add an add-only “Course people” panel to `/dashboard/admin/courses`.
  - Admin selects a course from the course directory via an `Add people` action.
  - Student picker:
    - Fetch active student profiles from the selected course institution with `listUserProfiles({ institution_id, profile_type: 'student', status: 'active' })`.
    - Create enrollment using existing `createEnrollment({ student_profile_id, course_id, institution_id, enrolled_by_profile_id })`.
  - Instructor picker:
    - Fetch active instructors from the selected course institution.
    - Add frontend auth helper `createRoleAssignment` using `POST /api/auth/rbac/role-assignments/`.
    - Payload: `{ account_id: instructor.auth_account_id, role_code: 'instructor', scope_type: 'course', scope_id: course.id }`.
  - Super admins can add people to any listed course; institution admins can only add people to courses in their own institution through existing course list scoping.
  - Do not add remove/revoke roster controls in this change.

## Interfaces
- Add frontend auth API type/helper:
  - `RoleAssignmentPayload`
  - `createRoleAssignment(payload): Promise<RoleAssignment>`
- Reuse existing helpers:
  - `getCourse`, `getCourseStructure`
  - `listUserProfiles`
  - `createEnrollment`
- Add route:
  - `/dashboard/instructor/courses/:courseId`
- Keep existing `/dashboard/instructor/courses/:courseId/builder`.

## Test Plan
- Frontend tests:
  - Instructor courses page `Open` goes to course overview, not directly to builder.
  - Assigned instructor can open course overview and see course-local `Overview` and `Builder` links.
  - Assigned instructor can navigate from overview to builder.
  - Unassigned instructor cannot open overview or builder and does not call course detail/structure APIs.
  - Instructor pages render expected breadcrumbs.
  - Admin Courses can add a student by name and calls `createEnrollment` with selected IDs.
  - Admin Courses can add an instructor by name and calls `createRoleAssignment` with `role_code: 'instructor'`, `scope_type: 'course'`, and selected course ID.
  - Institution admin add-people pickers are scoped to their institution.
  - Existing admin course CRUD tests still pass.

- Verification:
  - `pnpm -C frontend typecheck`
  - `pnpm -C frontend test -- src/App.test.tsx`
  - `pnpm -C frontend lint`
  - `git diff --check`
  - Run headed Selenium with `SELENIUM_HEADLESS=false`, visible at `http://127.0.0.1:7900`, and cover instructor course open/overview/builder plus admin Courses add-people UI.

## Assumptions
- “Course page links in the left side menu” means a course-local left menu inside the instructor course workspace, while preserving the existing global Portal sidebar.
- “Add students” means create course enrollments.
- “Add instructor” means create course-scoped RBAC role assignments for active instructor profiles.
- This change is add-only for course people; no roster removal/revoke UI is included.
- No backend schema changes, migrations, or unrelated flow changes.
