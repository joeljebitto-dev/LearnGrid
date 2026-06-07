# T-002 Token And Session Security

Related spec: [SPEC-002](../specs/002-token-session-security.md)  
Related schema: [auth_db](../DATABASE_SCHEMA.md#auth_db)

- [x] T-002.01 Implement access token issuance.
- [x] T-002.02 Implement refresh token issuance and rotation.
- [x] T-002.03 Store refresh token hashes and token identifiers.
- [x] T-002.04 Implement logout token revocation.
- [x] T-002.05 Implement Redis-backed token blacklist checks.
- [x] T-002.06 Invalidate tokens after password change or admin revocation.
- [x] T-002.07 Add API tests for valid, expired, revoked, and malformed tokens.
- [x] T-002.08 Document token lifetime and blacklist TTL behavior.

## Verification Notes
- `auth-service` now exposes `POST /api/auth/token/issue/`, `POST /api/auth/token/refresh/`, `POST /api/auth/logout/`, and protected `GET /api/auth/session/`.
- Refresh tokens are persisted as HMAC-SHA-256 hashes and raw refresh tokens are not stored.
- Token revocation writes durable `token_blacklist` rows and Redis blacklist keys with remaining-lifetime TTL when Redis is available.
- Verification passed: Ruff, Django system check, migration dry-run, and pytest.
