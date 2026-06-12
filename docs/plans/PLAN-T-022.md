# T-022 Security Implementation Plan

## Summary
Implement a repo-wide security baseline without resolving `OD-003` deployment model or `OD-004` auth model. Harden gateway/Django production settings, require production secrets from environment/Secret refs, strengthen validation, add durable admin audit coverage, add optional upload malware scanning, add security tests and backup restore verification, and add Kubernetes security-only baseline templates.

## Key Changes
- **Gateway and headers**
  - Extend Nginx with HSTS, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, a local-dev-compatible CSP, `Vary: Origin`, and stricter CORS denial tests.
  - Keep HTTP-to-HTTPS redirect and local TLS flow; add an ingress security template with TLS/SSL-redirect/HSTS annotations for future T-023 deployments.

- **Secrets and production settings**
  - Add a small shared security helper package for env parsing, required production env checks, and Django security defaults.
  - Update all backend `production.py` files to require `DJANGO_SECRET_KEY`, `DATABASE_URL`, `DJANGO_ALLOWED_HOSTS`, and service-specific sensitive envs; no insecure production fallback.
  - Enforce secure proxy/cookie/header settings in production: SSL redirect, `SECURE_PROXY_SSL_HEADER`, HSTS, secure session/CSRF cookies, content sniffing protection, frame denial, and strict referrer policy.
  - Keep bearer-token JWT auth unchanged; document that CSRF enforcement becomes required only if `OD-004` chooses cookie-based auth.

- **Validation, audit, and uploads**
  - Enforce Django password validation for auth account creation and password reset confirmation; set `AUTH_PASSWORD_MIN_LENGTH=12` and mirror this in frontend Zod validation.
  - Tighten sensitive serializer fields: token max lengths, phone format, upload file name/object key validation, MIME/extension allowlists, and request-size settings.
  - Extend auth durable audit logs for admin account create/update/deactivate using the existing authorization audit table plus Kafka auth events.
  - Keep existing durable audit coverage for login attempts, RBAC changes, enrollment history, and grade history; add focused regression tests around those guarantees.
  - Add content upload security settings: `CONTENT_ALLOWED_FILE_EXTENSIONS`, `CONTENT_MALWARE_SCAN_ENABLED=false`, `CONTENT_MALWARE_SCANNER_COMMAND`, and `CONTENT_MALWARE_SCAN_TIMEOUT_SECONDS=10`.
  - When scanning is enabled, uploads fail closed on scanner error/timeout/nonzero result; proxy uploads scan a temporary local file, and presigned/object-key flows pass object metadata for an external scanner hook.

- **Kubernetes security baseline**
  - Add `infrastructure/kubernetes/security-baseline/` templates only: namespace pod-security labels, per-service ServiceAccounts with no default API permissions, Secret/ConfigMap reference examples, default-deny NetworkPolicy examples, restricted pod security context snippets, and ingress security template.
  - Do not create full Deployments/Services/HPAs; those remain T-023 after `OD-003`.

- **Docs and task state**
  - Add `docs/security-design/SEC-022-security.md`.
  - Update `.env.example`, service `.env.example` files, API/development/backend/testing docs, changelog, living document, and `docs/tasks/T-022-security.md`.
  - Mark `T-022.01` through `T-022.08` complete after verification, with notes that full deployment manifests and production rollout verification stay under T-023/OD-003.

## Tests and Verification
- Add shared security helper tests for env parsing, production secret validation, and secure-setting defaults.
- Add gateway/security tests for HTTPS redirect, CORS allow/deny, required headers, CSP, and request-size controls.
- Add auth tests for password validation, admin audit rows, login audit/rate-limit behavior, and protected API negative paths.
- Add content tests for MIME/extension rejection, unsafe object keys, scan disabled behavior, scan success, scan failure, and scanner outage fail-closed behavior.
- Add repo security tests for Kubernetes baseline templates, absence of real secrets in tracked production templates, and backup restore script syntax.
- Add `scripts/verify-postgres-backup-restore.sh` to dump each service DB, restore into temporary restore-check DBs, run a smoke query, and drop the temporary DBs.
- Update CI with a security job running repo security tests, gateway tests, shell syntax checks, and the backup restore script against local Compose PostgreSQL.
- Verification commands: frontend lint/typecheck/test/build; each changed backend service `poetry lock`, Ruff, Django check, migration dry run, pytest; shared package Ruff/pytest; gateway/security pytest; backup restore script; `git diff --check`.

## Assumptions
- Use Kubernetes security baseline templates now; full Kubernetes deployments remain T-023.
- JWT bearer auth remains the current auth model; no cookie auth or OAuth/SSO changes in T-022.
- Local development examples may keep clearly labeled local-only placeholder secrets; production settings must not accept insecure defaults.
- Malware scanning is optional and disabled by default, but fails closed when enabled.
