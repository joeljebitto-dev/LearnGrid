# SPEC-022 Security

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-022](../tasks/T-022-security.md)  
Related schemas: [DATABASE_SCHEMA.md](../DATABASE_SCHEMA.md)

## Functional Requirements
- SPEC-022-FR-001 All external traffic shall use HTTPS.
- SPEC-022-FR-002 Secrets shall be stored in Kubernetes Secrets, sealed secrets, or Vault, not source code.
- SPEC-022-FR-003 All inputs shall be validated through serializers, schema validation, and frontend form validation.
- SPEC-022-FR-004 CORS restrictions shall be enforced.
- SPEC-022-FR-005 Sensitive endpoints shall be protected by authentication, authorization, rate limiting, and audit logs.
- SPEC-022-FR-006 Uploaded files shall be validated for type and size.
- SPEC-022-FR-007 Uploaded files may be scanned for malware.
- SPEC-022-FR-008 Audit logs shall cover login attempts, permission changes, enrollment changes, grade changes, and administrative actions.
- SPEC-022-FR-009 CSRF protection shall be used where cookie-based authentication is used.
- SPEC-022-FR-010 Secure headers shall be configured.
- SPEC-022-FR-011 Database backups and restore testing shall be implemented.
- SPEC-022-FR-012 Least-privilege service accounts shall be used.

## Non-Functional Requirements
- SPEC-022-NFR-001 Authorization checks shall be enforced on backend services.
- SPEC-022-NFR-002 Audit logs shall be tamper-resistant from normal application workflows.
- SPEC-022-NFR-003 Security checks shall run in CI/CD.

## Acceptance Criteria
- SPEC-022-AC-001 Protected APIs reject unauthenticated and unauthorized requests.
- SPEC-022-AC-002 Secrets are absent from source-controlled configuration.
- SPEC-022-AC-003 Sensitive writes produce audit logs.
- SPEC-022-AC-004 File upload validation rejects unsafe files.
- SPEC-022-AC-005 Restore testing confirms backup usability.
