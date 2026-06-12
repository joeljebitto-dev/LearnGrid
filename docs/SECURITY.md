# LearnGrid Security

Source design: [security-design/SEC-022-security.md](security-design/SEC-022-security.md)  
Related task: [T-022](tasks/T-022-security.md)

## Authentication
- API authentication uses short-lived JWT access tokens and rotating refresh tokens.
- Optional generic OIDC login is enabled only when `AUTH_OIDC_ENABLED=true`.
- OIDC matches existing active accounts by verified email or an existing `issuer + subject`
  external identity. It does not create accounts, profiles, or roles.
- Frontend SSO uses `/auth/oidc/callback` and stores the returned token pair through the same
  baseline token storage path as email/password login.

## Authorization
- `auth-service` owns RBAC roles, permissions, scoped role assignments, permission cache
  invalidation, and authorization audit logs.
- Non-auth services validate JWTs locally and call `auth-service` for scoped authorization checks.
- Authorization failures and auth-service network failures deny by default.

## Runtime Security
- Nginx gateway enforces local HTTPS redirect, CORS, request-size limits, rate limits, JSON access
  logs, and browser security headers.
- Production Django settings reject local placeholder secrets and require runtime-provided
  `DJANGO_SECRET_KEY`, `DATABASE_URL`, allowed hosts, and service secrets.
- Redis Sentinel is the production Redis HA mode; local development uses direct `REDIS_URL`.
- MinIO signed URLs are the selected video/content delivery strategy.

## Verification
- Security tests live under [tests/security/](../tests/security/).
- Backup restore verification uses [scripts/verify-postgres-backup-restore.sh](../scripts/verify-postgres-backup-restore.sh).
- Staging and performance evidence use [scripts/verify-staging-release.sh](../scripts/verify-staging-release.sh)
  and [scripts/verify-performance-gates.sh](../scripts/verify-performance-gates.sh).
