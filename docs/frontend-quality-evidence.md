# LearnGrid Frontend Quality Evidence

Related tasks: [T-025](tasks/T-025-frontend-feature-completion.md), [T-027](tasks/T-027-production-readiness-evidence.md), [T-028](tasks/T-028-ui-design-system-and-product-ux.md), [T-029](tasks/T-029-accessibility-and-frontend-quality.md)
Related docs: [FRONTEND_ARCHITECTURE.md](FRONTEND_ARCHITECTURE.md), [frontend-design-system.md](frontend-design-system.md), [TESTING_STRATEGY.md](TESTING_STRATEGY.md)

## FQE-001 Implemented Quality Controls
- Skip link to `#main-content` is provided through `FrontendQualityShell`.
- Portal, login, SSO callback, no-access, and route-error surfaces expose landmarks and controlled status/error messaging.
- Shared `FormField` wires help and error text through `aria-describedby`, announces errors through `role="alert"`, and marks invalid controls with `aria-invalid`.
- Shared loading, skeleton, retry, permission-denied, and network/session banners use live regions or status roles.
- `Modal` and `Drawer` support initial focus, Escape dismissal when `onClose` is supplied, and focus restoration.
- `DataTable` supports captions and scoped column headers.
- Reduced-motion handling is defined in `frontend/src/styles.css`.
- Axios emits session-expired and network-error events; the quality shell renders user-safe messages.
- Route-level rendering failures are contained by `RouteErrorBoundary` and reported through the Sentry helper with route tags.
- Unsaved-change protection is enabled for course builder, assessment authoring, quiz attempts, assignment submissions, grading workflows, and report generation forms.

## FQE-002 Automated Checks
Run:

```bash
pnpm -C frontend lint
pnpm -C frontend typecheck
pnpm -C frontend test
pnpm -C frontend build
```

Implemented tests include:
- `frontend/src/features/design-system/accessibility.test.tsx`: `jest-axe` scan of the component preview.
- `frontend/src/features/shared/quality.test.tsx`: skip link, session expiry, network message, route error boundary, and unsaved-change behavior.
- `frontend/src/features/shared/ui.test.tsx`: form ARIA wiring, disabled reason, pagination, status badge, and empty-state behavior.
- Existing route tests cover role navigation, portal access, loading, retry, API failure, and feature-route smoke behavior.

## FQE-003 Manual Review Matrix
Manual QA should use this matrix before attaching final production-readiness evidence to [T-027](tasks/T-027-production-readiness-evidence.md).

| Area | Evidence expected | Current repo artifact |
| --- | --- | --- |
| Keyboard navigation | Login, dashboard, catalog, player, authoring, attempts, grading, certificates, notifications, and reports can be operated with Tab, Shift+Tab, Enter, Space, and Escape where relevant | Shared focus states, route tests, quality tests |
| Screen readers | Form fields expose labels, descriptions, errors, loading, saving, retry, network, no-access, and session expiry messages | `FormField`, `LiveRegion`, `ErrorState`, `FrontendQualityShell` |
| Contrast | Brand, status, disabled, error, dashboard, and focus colors use high-contrast Tailwind tokens | `tailwind.config.js`, `styles.css`, design preview |
| Responsive behavior | 390px, 768px, 1024px, and 1440px viewport smoke checks for student, instructor, and admin journeys | Responsive grid/classes and Selenium smoke plan |
| Cross-browser smoke | Chromium, Firefox, and WebKit/Safari-equivalent smoke checks for login, navigation, forms, and modals | Manual evidence remains attached under T-027 once run |
| Role-based UX acceptance | Student, instructor, institution admin, and super admin see expected navigation and no unrelated portal links | Existing frontend route tests |
| Production artifacts | Screenshots, browser/driver versions, test output, and reviewer signoff | Tracked by T-027 production evidence |

## FQE-004 Known Boundaries
- Frontend permission UI is not authoritative; backend authorization remains the security control.
- Visual regression screenshots are not stored as baseline artifacts yet. Use this evidence document plus Selenium and production-readiness artifacts until a stable screenshot workflow is adopted.
- Real staging browser evidence and performance evidence remain linked to [T-027](tasks/T-027-production-readiness-evidence.md).
