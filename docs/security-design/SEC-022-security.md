# SEC-022 Security Baseline

Related task: [T-022 Security](../tasks/T-022-security.md)  
Related spec: [SPEC-022 Security](../specs/022-security.md)

T-022 established the shared security baseline before the later T-023 on-prem Kubernetes decision.
[OD-004 Authentication Model](../KNOWN_ISSUES.md#od-004-authentication-model) remains open.

## Runtime Controls
- The local Nginx gateway redirects HTTP to HTTPS, terminates local TLS, restricts CORS to local
  development origins, rate limits API traffic, caps request bodies, and emits browser security
  headers including HSTS, nosniff, frame denial, referrer policy, permissions policy, CSP, and
  `Vary: Origin`.
- Production Django settings for every backend service require `DJANGO_SECRET_KEY`,
  `DATABASE_URL`, `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and service-specific secrets.
  Local-only placeholder secret values are rejected by production settings.
- JWT bearer authentication remains the implemented auth model. CSRF trusted origins and secure
  CSRF cookies are configured for production, but CSRF enforcement for authenticated API writes is
  deferred unless `OD-004` selects cookie-based authentication.

## Secrets And Service Accounts
- Secrets are represented by Kubernetes Secret, SealedSecret, or Vault-managed references. Tracked
  Kubernetes templates use placeholders only.
- `infrastructure/kubernetes/security-baseline/` provides security-only templates for namespace pod
  security labels, per-workload ServiceAccounts, default-deny NetworkPolicy examples, restricted
  pod security context snippets, and TLS ingress annotations.
- Full Deployments, Services, HPAs, probes, and rollout wiring are implemented by the T-023 Helm
  baseline.

## Validation, Audit, And Upload Security
- Auth and user profile account-creation inputs enforce a 12-character minimum password policy.
  Auth-service also applies Django password validators before hashing temporary or reset passwords.
- Sensitive token fields, phone numbers, upload object keys, file names, MIME types, extensions, and
  request sizes are validated through serializers and service checks.
- Login attempts, password reset actions, RBAC permission changes, enrollment transitions, grade
  changes, and admin account lifecycle changes have durable audit records.
- Content upload malware scanning is optional. When `CONTENT_MALWARE_SCAN_ENABLED=true`, scanner
  errors, timeouts, or nonzero results fail closed. Proxy uploads scan a temporary local file;
  object-storage flows pass object metadata and the object key to the configured scanner command.

## Backup Restore Verification
- `scripts/verify-postgres-backup-restore.sh` dumps every service database from local Compose
  PostgreSQL, restores each dump into a temporary restore-check database, runs a smoke query, and
  drops the temporary database.
- CI runs static security tests and backup restore verification against the local PostgreSQL
  service. Production backup cadence and PITR implementation remain under T-023.
