# Admin Institutions CRUD

## Summary
Add an **Institutions** link to the admin Portal nav and create `/dashboard/admin/institutions` for institution CRUD. Reuse the existing `user-service` institution endpoints; no backend/schema changes are needed.

## Key Changes
- Add frontend institution types and API helpers in `frontend/src/api/users.ts`:
  - `listInstitutions`, `createInstitution`, `updateInstitution`, `archiveInstitution`
  - status values: `active`, `suspended`, `archived`
- Add `AdminInstitutionsPage` under the admin feature area:
  - Paginated/searchable institution list showing `name`, `code`, and `status`
  - Create/edit form with only `name`, `code`, and `status`
  - Archive/delete action calls existing `DELETE /api/users/institutions/<id>/`
  - After create/update/archive, invalidate/refetch institution queries
- Wire routing and navigation:
  - Add `/dashboard/admin/institutions` as a protected admin route
  - Add `Institutions` to the admin Portal nav with active key `admin-institutions`
- Keep all other flows unchanged:
  - No backend edits
  - No database migrations
  - Do not touch unrelated modified `docker-compose.yml`

## Test Plan
- Update `frontend/src/App.test.tsx` mocks for the new institution API helpers.
- Add tests covering:
  - Admin Portal nav includes `Institutions`
  - Super admin can view, create, edit, and archive institutions
  - Institution admin does not get CRUD controls/API calls if frontend-gated
  - Non-admin users still cannot access admin institution routes
  - Existing create-user/admin navigation tests still pass
- Run verification:
  - `pnpm -C frontend typecheck`
  - `pnpm -C frontend test -- src/App.test.tsx`
  - `pnpm -C frontend lint`
- Note: current shell check found `pnpm` unavailable, so verification must run once the package manager is available in the implementation environment.

## Assumptions
- “CURD” means CRUD.
- “Delete” uses the existing soft-delete/archive backend behavior.
- The frontend will expose only `name`, `code`, and `status`; backend `settings` remains untouched/defaulted.
- The backend remains the source of truth for authorization; frontend gating should prevent institution admins from attempting platform-level institution CRUD.
