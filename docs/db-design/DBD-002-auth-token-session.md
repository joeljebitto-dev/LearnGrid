# DBD-002 Auth Token And Session

Related task: [T-002 Token And Session Security](../tasks/T-002-token-session-security.md)  
Related spec: [SPEC-002 Token Session Security](../specs/002-token-session-security.md)  
Canonical schema: [auth_db](../DATABASE_SCHEMA.md#auth_db)

## Design Summary
T-002 implemented token and session persistence inside `auth_db`. `auth-service` owns account identity, password credentials, refresh token storage, token blacklist records, and login audit records. Repository closure adds OIDC external identity links for existing-account SSO.

## Implemented Tables
| Table ID | Table | Purpose |
| --- | --- | --- |
| `DB-AUTH-001` | `accounts` | Login identity and account status |
| `DB-AUTH-002` | `credentials` | Password hash and password-change invalidation timestamp |
| `DB-AUTH-003` | `refresh_tokens` | Persisted refresh token JTI, hash, expiry, device, and revocation state |
| `DB-AUTH-004` | `token_blacklist` | Durable blacklist fallback for revoked access and refresh token JTIs |
| `DB-AUTH-006` | `login_audit_logs` | Login, logout, refresh, and password reset audit events |
| `DB-AUTH-012` | `external_identities` | Verified OIDC `issuer + subject` links to existing active accounts |

`DB-AUTH-005 password_reset_tokens` remains documented in the canonical schema for later password reset work, but was not implemented as part of T-002.

## Storage Rules
- Passwords are stored only as secure hashes in `credentials.password_hash`.
- Refresh tokens are stored only as HMAC-SHA-256 hashes in `refresh_tokens.token_hash`.
- JWTs include account UUID, token type, JTI, issue/expiry timestamps, and password-change timestamp.
- `credentials.password_changed_at` invalidates older access and refresh tokens after password changes or account-level revocation.
- OIDC links are stored only after provider signature, issuer, audience, nonce, and verified-email checks pass; no user is auto-provisioned.

## Indexes And Constraints
- `accounts.email` is unique; `accounts.phone` is unique when present.
- `credentials.account_id` is a one-to-one relationship.
- `refresh_tokens.token_jti` is unique and indexed by account and expiry.
- `token_blacklist.token_jti` is unique and indexed by expiry for cleanup.
- `login_audit_logs` is indexed by account/time, event type, and attempted email.

## Redis And Fallback
Revoked token JTIs are written to Redis with a TTL equal to the remaining token lifetime. The same JTI is persisted in `token_blacklist`, so blacklist checks fall back to the database when Redis is unavailable.

## Verification
T-002 tests cover token issue, refresh rotation, logout revocation, malformed/expired/revoked tokens, password-change invalidation, admin revocation, Redis blacklist behavior, database fallback, and refresh token hash storage.
