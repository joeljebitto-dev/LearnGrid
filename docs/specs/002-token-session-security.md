# SPEC-002 Token And Session Security

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-002](../tasks/T-002-token-session-security.md)  
Related schema: [auth_db](../DATABASE_SCHEMA.md#auth_db)  
Open decision: [OD-004 Authentication Model](../KNOWN_ISSUES.md#od-004-authentication-model)

## Functional Requirements
- SPEC-002-FR-001 The system shall support JWT-based authentication using access and refresh tokens.
- SPEC-002-FR-002 The system shall support refresh token persistence and revocation.
- SPEC-002-FR-003 The system shall support token blacklist behavior using Redis and durable records where needed.
- SPEC-002-FR-004 The system shall invalidate tokens after logout, password change, administrative revocation, or detected compromise.
- SPEC-002-FR-005 The system shall store token hashes or token identifiers, not raw token secrets.

## Non-Functional Requirements
- SPEC-002-NFR-001 Token validation shall avoid unnecessary database queries for common authenticated requests.
- SPEC-002-NFR-002 Token blacklist entries shall have TTL-aligned expiry.
- SPEC-002-NFR-003 Sensitive token operations shall be audited.

## Token Lifetime Defaults
- SPEC-002-CONFIG-001 Access tokens default to 5 minutes and are configured with `AUTH_ACCESS_TOKEN_LIFETIME_SECONDS`.
- SPEC-002-CONFIG-002 Refresh tokens default to 7 days and are configured with `AUTH_REFRESH_TOKEN_LIFETIME_SECONDS`.
- SPEC-002-CONFIG-003 JWTs are signed by auth-service using `HS256` and issuer `AUTH_JWT_ISSUER`.
- SPEC-002-CONFIG-004 Refresh tokens are stored as HMAC-SHA-256 hashes; raw refresh tokens are never stored.
- SPEC-002-CONFIG-005 Logout, refresh rotation, password changes, and admin revocation persist durable blacklist records and write Redis blacklist keys with TTL equal to the remaining token lifetime.
- SPEC-002-CONFIG-006 If Redis is unavailable, auth-service falls back to the durable `token_blacklist` table for blacklist checks.

## Acceptance Criteria
- SPEC-002-AC-001 Access tokens authorize protected API calls until expiry or blacklist state invalidates them.
- SPEC-002-AC-002 Refresh tokens can rotate and old refresh tokens become unusable.
- SPEC-002-AC-003 Revoked tokens are rejected by protected endpoints.
- SPEC-002-AC-004 Token blacklist cleanup can remove expired records safely.
