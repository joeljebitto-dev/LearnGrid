# SPEC-001 Authentication Lifecycle

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-001](../tasks/T-001-project-setup.md)  
Related schema: [auth_db](../DATABASE_SCHEMA.md#auth_db)  
Open decision: [OD-004 Authentication Model](../KNOWN_ISSUES.md#od-004-authentication-model)

## Functional Requirements
- SPEC-001-FR-001 The system shall allow users to register.
- SPEC-001-FR-002 The system shall allow users to log in.
- SPEC-001-FR-003 The system shall allow users to log out.
- SPEC-001-FR-004 The system shall allow users to reset passwords.
- SPEC-001-FR-005 The system shall record authentication audit events for login, logout, token refresh, and password reset activity.
- SPEC-001-FR-006 The system shall support account states including pending, active, locked, disabled, and deactivated.

## Non-Functional Requirements
- SPEC-001-NFR-001 Authentication endpoints shall validate all inputs through backend serializers.
- SPEC-001-NFR-002 Login, OTP, and password reset endpoints shall be rate limited through Redis.
- SPEC-001-NFR-003 Passwords shall be stored only as secure hashes.

## Acceptance Criteria
- SPEC-001-AC-001 A user can complete registration and receive an active or pending account based on configured workflow.
- SPEC-001-AC-002 A valid user can log in and receive tokens according to [SPEC-002](002-token-session-security.md).
- SPEC-001-AC-003 Logout invalidates the active refresh/session state.
- SPEC-001-AC-004 Password reset tokens expire and cannot be reused.
- SPEC-001-AC-005 Failed login attempts are audited and rate limited.
