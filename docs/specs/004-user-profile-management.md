# SPEC-004 User And Profile Management

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-004](../tasks/T-004-user-profile-management.md)  
Related schema: [user_db](../DATABASE_SCHEMA.md#user_db)

## Functional Requirements
- SPEC-004-FR-001 Administrators shall create users.
- SPEC-004-FR-002 Administrators shall update users.
- SPEC-004-FR-003 Administrators shall deactivate users.
- SPEC-004-FR-004 Administrators shall search users.
- SPEC-004-FR-005 The system shall maintain profile data separately from authentication credentials.
- SPEC-004-FR-006 The system shall support student, instructor, admin, and organization-specific profile attributes.
- SPEC-004-FR-007 The system shall support future bulk import of users through CSV or Excel.

## Non-Functional Requirements
- SPEC-004-NFR-001 User list APIs shall support pagination, filtering, and sorting.
- SPEC-004-NFR-002 Profile search fields shall be indexed.
- SPEC-004-NFR-003 Profile operations shall respect institution scope and backend authorization.

## Acceptance Criteria
- SPEC-004-AC-001 Admin users can create profiles linked to authentication accounts.
- SPEC-004-AC-002 Deactivated users cannot access protected platform areas.
- SPEC-004-AC-003 Search supports institution-scoped user lookup.
- SPEC-004-AC-004 Role-specific profile data is stored in the correct profile table.
