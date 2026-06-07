# Database Design Documents

These documents capture implemented database design decisions for LearnGrid LMS.
The canonical full table and field reference remains [DATABASE_SCHEMA.md](../DATABASE_SCHEMA.md).

## Numbering
Database design documents use stable IDs:

- `DBD-001` for project setup and service database ownership.
- `DBD-002` onward for implemented feature database designs.

## Implemented Designs
| ID | Design | Related task | Related spec |
| --- | --- | --- | --- |
| [DBD-001](DBD-001-service-databases.md) | Service Databases | [T-001](../tasks/T-001-project-setup.md) | [SPEC-001](../specs/001-authentication-lifecycle.md) |
| [DBD-002](DBD-002-auth-token-session.md) | Auth Token And Session | [T-002](../tasks/T-002-token-session-security.md) | [SPEC-002](../specs/002-token-session-security.md) |
| [DBD-003](DBD-003-rbac-authorization.md) | RBAC Authorization | [T-003](../tasks/T-003-rbac-object-authorization.md) | [SPEC-003](../specs/003-rbac-object-authorization.md) |
| [DBD-004](DBD-004-user-profile-management.md) | User Profile Management | [T-004](../tasks/T-004-user-profile-management.md) | [SPEC-004](../specs/004-user-profile-management.md) |
| [DBD-005](DBD-005-institution-batch-department-management.md) | Institution, Batch, And Department Management | [T-005](../tasks/T-005-institution-batch-department-management.md) | [SPEC-005](../specs/005-institution-batch-department-management.md) |

## Rules
- Keep [DATABASE_SCHEMA.md](../DATABASE_SCHEMA.md) as the field-level source of truth.
- Add one `DBD-###-<topic>.md` file after a task with database design is implemented.
- Link every design file to its related task, spec, and schema section.
- Do not add future task designs as implemented until their task checklist is complete.
