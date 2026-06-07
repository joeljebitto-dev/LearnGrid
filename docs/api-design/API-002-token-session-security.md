# API-002 Token Session Security

Related task: [T-002 Token And Session Security](../tasks/T-002-token-session-security.md)  
Related spec: [SPEC-002 Token Session Security](../specs/002-token-session-security.md)  
Related database design: [DBD-002](../db-design/DBD-002-auth-token-session.md)

## Design Summary
T-002 implemented JWT access and refresh token APIs in `auth-service`. Access tokens are short lived, refresh tokens rotate, and logout/admin revocation invalidates active tokens.

## Endpoints
| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/auth/token/issue/` | Public | Issue access and refresh token pair |
| `POST` | `/api/auth/token/refresh/` | Public | Rotate refresh token and issue a new pair |
| `POST` | `/api/auth/logout/` | Public token payload | Revoke refresh token and optional access token |
| `GET` | `/api/auth/session/` | Access token | Return current account identity |

## Request And Response Shapes
Token issue request:

```json
{ "email": "student@example.com", "password": "secret", "device_label": "Laptop" }
```

Token issue and refresh response:

```json
{
  "access": "<jwt>",
  "refresh": "<jwt>",
  "access_expires_at": "<iso>",
  "refresh_expires_at": "<iso>"
}
```

Logout request:

```json
{ "refresh": "<jwt>", "access": "<jwt>" }
```

Logout response:

```json
{ "status": "revoked" }
```

Session response:

```json
{ "account_id": "<uuid>", "email": "student@example.com", "status": "active" }
```

## Auth And Failure Behavior
- JWT algorithm is `HS256`.
- Default access lifetime is 5 minutes; default refresh lifetime is 7 days.
- Refresh rotation revokes the previous refresh token.
- Malformed, expired, revoked, wrong-type, or password-stale tokens are rejected.
- Redis blacklist checks use database fallback through `token_blacklist`.

## Verification
T-002 tests cover successful issuance, session access, refresh rotation, logout revocation, malformed and expired tokens, password-change invalidation, admin revocation, Redis blacklist writes/checks, database fallback, and refresh token hash storage.
