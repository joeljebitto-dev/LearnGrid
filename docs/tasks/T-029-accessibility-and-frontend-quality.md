# T-029 Accessibility And Frontend Quality

Related specs: [SPEC-011](../specs/011-dashboards-portals.md), [SPEC-024](../specs/024-testing-quality.md)
Related docs: [FRONTEND_ARCHITECTURE.md](../FRONTEND_ARCHITECTURE.md), [TESTING_STRATEGY.md](../TESTING_STRATEGY.md), [DEVELOPMENT.md](../DEVELOPMENT.md)
Related tasks: [T-025](T-025-frontend-feature-completion.md), [T-027](T-027-production-readiness-evidence.md), [T-028](T-028-ui-design-system-and-product-ux.md)

- [x] T-029.01 Verify keyboard navigation across login, dashboards, catalog, learning player, authoring, attempts, submissions, grading, certificates, notifications, and reports.
- [x] T-029.02 Standardize visible focus states for links, buttons, form fields, menus, tabs, tables, modals, drawers, and destructive actions.
- [x] T-029.03 Add proper labels, descriptions, `aria-*` attributes, field IDs, and screen-reader form error announcements across major forms.
- [x] T-029.04 Validate color contrast for text, icons, focus rings, status colors, disabled states, charts, and dashboard metric cards.
- [x] T-029.05 Add screen-reader-friendly status messages for loading, saving, autosave, submit, upload, retry, permission denial, and destructive confirmation flows.
- [x] T-029.06 Add skip links, landmark structure, modal/drawer focus trapping, escape behavior, table captions, table headers, and reduced-motion handling where relevant.
- [x] T-029.07 Standardize loading, skeleton, retry, empty, no-access, error, and disabled-with-reason behavior across all frontend feature routes.
- [x] T-029.08 Add mutation pending states, duplicate-submit prevention, safe optimistic updates, and clear rollback/error behavior for create, update, delete, submit, upload, and publish actions.
- [x] T-029.09 Add session expiry handling, offline/network-error messaging, route-level error boundaries, and normalized backend validation error presentation.
- [x] T-029.10 Add unsaved-change protection and autosave UX for course authoring, assessment authoring, quiz attempts, assignment submissions, grading reviews, and report generation where applicable.
- [x] T-029.11 Align frontend telemetry and error reporting with the existing Sentry/OpenTelemetry direction, including user-safe error context and route/action tags.
- [x] T-029.12 Add automated accessibility checks where practical and expand frontend tests for loading, error, empty, retry, denied, responsive, keyboard, and form-error states.
- [x] T-029.13 Capture design QA evidence with cross-browser smoke checks, responsive viewport checks, role-based UX acceptance flows, product acceptance checklist, UX review signoff, and production-readiness artifacts.

Notes:
- T-029 is a frontend quality and evidence task. It does not add new product APIs or replace backend authorization.
- New automated checks should fail on real regressions but avoid brittle assertions tied to incidental layout details.
- Visual regression or screenshot testing should be added only if the project adopts a stable baseline workflow; otherwise use documented screenshots and role-based UX acceptance evidence.
- Completion evidence must include automated test output, manual accessibility review results, responsive screenshots or equivalent artifacts, and linked production-readiness evidence under T-027 where applicable.
- Implemented evidence is documented in [frontend-quality-evidence.md](../frontend-quality-evidence.md). Verification completed with `pnpm -C frontend lint`, `pnpm -C frontend typecheck`, `pnpm -C frontend test`, and `pnpm -C frontend build`.
