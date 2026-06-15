# T-028 UI Design System And Product UX

Related specs: [SPEC-006](../specs/006-course-catalog-metadata.md), [SPEC-007](../specs/007-course-structure-versioning.md), [SPEC-008](../specs/008-content-upload-storage-access.md), [SPEC-011](../specs/011-dashboards-portals.md), [SPEC-012](../specs/012-assessment-authoring.md), [SPEC-013](../specs/013-quiz-attempts-exams.md), [SPEC-014](../specs/014-assignment-submissions.md), [SPEC-015](../specs/015-grading-results-audit.md), [SPEC-016](../specs/016-certificates.md), [SPEC-017](../specs/017-notifications.md), [SPEC-018](../specs/018-search-reporting-analytics.md), [SPEC-024](../specs/024-testing-quality.md)
Related docs: [FRONTEND_ARCHITECTURE.md](../FRONTEND_ARCHITECTURE.md), [TESTING_STRATEGY.md](../TESTING_STRATEGY.md)
Related task: [T-025](T-025-frontend-feature-completion.md)

- [x] T-028.01 Define LearnGrid design tokens for spacing, radius, shadow, typography, colors, status colors, and responsive breakpoints.
- [x] T-028.02 Build reusable button variants with loading, disabled, destructive, secondary, ghost, icon, and focus states.
- [x] T-028.03 Build reusable form controls for input, select, textarea, checkbox, radio, date, and time fields.
- [x] T-028.04 Build a `FormField` abstraction with label, help text, error text, required marker, IDs, and accessibility attributes.
- [x] T-028.05 Build layout primitives for page headers, sections, panels, cards, toolbars, dividers, portal shells, and responsive content grids.
- [x] T-028.06 Build feedback primitives for badges, status chips, tags, avatars, tooltips, toasts, modals, drawers, tabs, breadcrumbs, pagination, and tables.
- [x] T-028.07 Build standard loading skeletons, error states, empty states, retry states, permission-denied states, and disabled-with-reason states.
- [x] T-028.08 Build dashboard metric cards and role-aware dashboard layout primitives for student, instructor, institution admin, and super admin portals.
- [x] T-028.09 Build LMS course components for course cards, catalog filters, course detail headers, outcomes, prerequisites, modules, lessons, enrollment CTAs, and progress indicators.
- [x] T-028.10 Build course authoring components for module, lesson, and topic trees with reorder affordances, publish state, content attachment state, and validation feedback.
- [x] T-028.11 Build lesson player components for content navigation, completion state, video/document display, progress updates, and access-denied messaging.
- [x] T-028.12 Build assessment authoring components for question banks, question editors, quiz/exam configuration, publish/close state, and validation feedback.
- [x] T-028.13 Build student attempt and assignment components for timers, autosave indicators, question navigation, draft/save/submit/resubmit flows, confirmations, deadlines, late state, and closed state.
- [x] T-028.14 Build grading, certificate, notification, and analytics product components for rubrics, comments, overrides, published visibility, certificate status, unread/read state, preferences, reporting filters, and report snapshots.
- [x] T-028.15 Improve visual hierarchy with stronger page headers, contextual descriptions, breadcrumbs for nested workflows, role-aware navigation, domain-specific icons, useful empty-state CTAs, and user-friendly API error messages.
- [x] T-028.16 Add component-level tests and component-preview documentation through Storybook or an adopted equivalent before treating the design system as reusable.

Notes:
- T-025 tracks feature-route completion. T-028 tracks reusable UI system quality and LMS-specific product polish on top of those completed routes.
- Do not duplicate feature implementation checklists from T-025; use this task to improve consistency, reuse, visual hierarchy, and product-specific interaction design.
- Dark-mode readiness is deferred unless a future product direction explicitly selects it.
- Completion evidence must include component tests, preview documentation, screenshots or review artifacts for representative components, and verified usage across student, instructor, institution admin, and super admin workflows.
- Frontend permission UI must improve feedback only; backend authorization remains authoritative.
- Implemented design-system evidence is documented in [frontend-design-system.md](../frontend-design-system.md). Verification completed with `pnpm -C frontend lint`, `pnpm -C frontend typecheck`, `pnpm -C frontend test`, `pnpm -C frontend build`, and `git diff --check`.
