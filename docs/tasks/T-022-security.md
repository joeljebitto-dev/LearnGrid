# T-022 Security

Related spec: [SPEC-022](../specs/022-security.md)  
Related schema: [DATABASE_SCHEMA.md](../DATABASE_SCHEMA.md)

- [x] T-022.01 Enforce HTTPS at gateway and ingress.
- [x] T-022.02 Move all secrets to Kubernetes Secrets, sealed secrets, or Vault.
- [x] T-022.03 Implement input validation on backend serializers and frontend forms.
- [x] T-022.04 Configure CORS and secure headers.
- [x] T-022.05 Implement audit logs for login attempts, permission changes, enrollment changes, grade changes, and admin actions.
- [x] T-022.06 Implement file upload security validation and optional malware scanning hook.
- [x] T-022.07 Configure least-privilege service accounts.
- [x] T-022.08 Add security tests and backup restore verification.

Notes:
- T-022 adds security-only Kubernetes baseline templates. Full Deployments, Services, HPAs,
  probes, and production backup/PITR wiring are now implemented under T-023; final staging rollout
  verification remains tracked by `T-023.06`.
- JWT bearer authentication remains the active auth model. Cookie-auth CSRF enforcement remains
  deferred until `OD-004 Authentication Model` is resolved.
