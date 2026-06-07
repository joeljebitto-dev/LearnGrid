# T-002 Token And Session Security Plan

## Summary
Implement `T-002` inside `auth-service` only. Add JWT access/refresh token issuance, refresh rotation, logout revocation, Redis-backed blacklist checks with durable database fallback, token invalidation after password changes/admin revocation, API tests, and token lifetime documentation. Keep `OD-004` open: this implements the JWT baseline but does not decide OAuth2 or SSO.

## Key Changes
- Add auth-service token models aligned with `DATABASE_SCHEMA.md`:
  - `Account`, `Credential`, `RefreshToken`, `TokenBlacklist`, and minimal `LoginAuditLog`
  - Store UUID public IDs, refresh token JTI, hashed refresh token value, expiry, revocation time, and audit metadata
  - Store password hashes in `Credential`, not raw passwords
- Add JWT service layer:
  - Sign access and refresh tokens with `HS256`
  - Include token type, `jti`, account UUID, issued/expiry timestamps, and password-change timestamp claim
  - Hash refresh tokens with HMAC/SHA-256 before database storage
  - Rotate refresh tokens by revoking the old refresh token and issuing a new access/refresh pair
  - Blacklist revoked access/refresh JTIs in Redis using TTL equal to remaining token lifetime, with DB fallback
- Add auth-service APIs:
  - `POST /api/auth/token/issue/` with `email`, `password`, optional `device_label`
  - `POST /api/auth/token/refresh/` with `refresh`
  - `POST /api/auth/logout/` with `refresh`, optional `access`
  - `GET /api/auth/session/` protected by access token, returns current account identity
- Update auth-service settings and routing:
  - Add token lifetime settings from environment variables
  - Add JWT auth class for protected DRF endpoints
  - Include authentication app URLs from service root URLs
- Add documentation/task updates:
  - Document access/refresh lifetimes, blacklist TTL behavior, token hash storage, and Redis/DB fallback
  - Mark `T-002.01` through `T-002.08` complete only after tests and checks pass

## Interfaces
- Token issue response:
  - `{ "access": "<jwt>", "refresh": "<jwt>", "access_expires_at": "<iso>", "refresh_expires_at": "<iso>" }`
- Token refresh response:
  - same shape as issue response; old refresh token becomes unusable
- Logout response:
  - `{ "status": "revoked" }`
- Session response:
  - `{ "account_id": "<uuid>", "email": "<email>", "status": "active" }`
- Default lifetimes:
  - Access token: 5 minutes
  - Refresh token: 7 days
  - Configurable through auth-service environment variables

## Test Plan
- Add migration and run `poetry run python manage.py check`.
- Run `poetry run ruff check .`.
- Run `poetry run pytest`.
- API tests must cover:
  - valid token issuance with correct access/refresh response
  - refresh token rotation and old refresh reuse rejection
  - logout revocation and revoked token rejection
  - malformed token rejection
  - expired token rejection
  - password-change invalidation
  - admin/account-level token revocation
  - Redis blacklist write/check behavior with DB fallback
  - refresh token database storage uses hashes, not raw token strings

## Assumptions
- `T-002` may add the minimal account and credential models needed to issue and validate tokens, even though full registration/password reset workflows remain for later tasks.
- JWT is implemented as the baseline required by `SPEC-002`; OAuth2/SSO remain unresolved under `OD-004`.
- Only `auth-service` changes are required for this task; other services will consume JWT validation later when their protected APIs are implemented.
