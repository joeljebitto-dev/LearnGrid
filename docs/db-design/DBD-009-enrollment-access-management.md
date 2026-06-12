# DBD-009 Enrollment And Access Management

Related task: [T-009](../tasks/T-009-enrollment-access-management.md)  
Related spec: [SPEC-009](../specs/009-enrollment-access-management.md)  
Canonical schema: [enrollment_db](../DATABASE_SCHEMA.md#enrollment_db)

## DBD-009-001 Scope
`enrollment-service` owns individual enrollments, batch and cohort enrollment jobs, immutable enrollment history, and derived access grants.

## DBD-009-002 Tables
| Table ID | Table | Purpose |
| --- | --- | --- |
| `DB-ENROLL-001` | `enrollments` | Student/course enrollment state |
| `DB-ENROLL-002` | `batch_enrollments` | Batch enrollment job summary |
| `DB-ENROLL-003` | `cohort_enrollments` | Cohort enrollment job summary |
| `DB-ENROLL-004` | `enrollment_history` | Status transition audit records |
| `DB-ENROLL-005` | `access_grants` | Active/revoked/suspended/expired course access |

## DBD-009-003 Notes
Student/course enrollment is unique. Status transitions append history and synchronize access grants. Student enrollment, removal, and access-expiry events use the shared Kafka-capable event design in [EVT-020](../event-design/EVT-020-kafka-eventing.md).
