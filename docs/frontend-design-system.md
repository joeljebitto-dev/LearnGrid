# LearnGrid Frontend Design System

Related tasks: [T-025](tasks/T-025-frontend-feature-completion.md), [T-028](tasks/T-028-ui-design-system-and-product-ux.md), [T-029](tasks/T-029-accessibility-and-frontend-quality.md)
Related docs: [FRONTEND_ARCHITECTURE.md](FRONTEND_ARCHITECTURE.md), [frontend-quality-evidence.md](frontend-quality-evidence.md), [TESTING_STRATEGY.md](TESTING_STRATEGY.md)

## DS-001 Scope
The implemented frontend design system lives in `frontend/src/features/shared/ui.tsx` with LMS-specific product components in `frontend/src/features/lms/LmsProductComponents.tsx`.

The adopted component-preview equivalent is `frontend/src/features/design-system/DesignSystemPreview.tsx`. It renders representative tokens, controls, layout primitives, feedback states, course components, assessment states, grading/certificate components, notifications, analytics filters, and data display examples.

## DS-002 Tokens
Tailwind tokens are defined in `frontend/tailwind.config.js`:
- Brand, ink, and status colors.
- Control and panel radius values.
- Panel and focus shadows.
- Page and section type scales.
- `xs` responsive breakpoint.

Global base styles are defined in `frontend/src/styles.css`, including focus-visible behavior, light color scheme, and application font stack.

## DS-003 Shared Primitives
Reusable primitives include:
- Buttons: primary, secondary, ghost, destructive, link, loading, disabled reason, and focus states.
- Forms: `FormField`, `Input`, `Select`, `Textarea`, checkbox, radio, date, time, and datetime controls.
- Layout: page headers, sections, panels, cards, toolbars, dividers, breadcrumbs, tabs, pagination, and tables.
- Feedback: badges, status chips, tags, avatars, tooltips, toasts, modals, drawers, skeletons, loading, error, empty, retry, permission-denied, and disabled-with-reason states.
- Dashboard: metric cards and summary grids.
- Icons: `lucide-react` is the frontend icon source for navigation and product component affordances.

## DS-004 LMS Components
Product components cover:
- Course cards, catalog filters, course detail headers, structure trees, lesson player layout, and progress indicators.
- Assessment authoring summary, attempt status, and assignment submission state.
- Grading review panels, rubric comment blocks, certificate cards, notification feed, reporting filters, and report insight panels.

## DS-005 Verification
Component tests are implemented beside the components:
- `frontend/src/features/shared/ui.test.tsx`
- `frontend/src/features/shared/quality.test.tsx`
- `frontend/src/features/lms/LmsProductComponents.test.tsx`
- `frontend/src/features/design-system/DesignSystemPreview.test.tsx`
- `frontend/src/features/design-system/accessibility.test.tsx`

Frontend verification commands:
```bash
pnpm -C frontend lint
pnpm -C frontend typecheck
pnpm -C frontend test
pnpm -C frontend build
```
