# SPEC-005 Institution, Batch, And Department Management

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-005](../tasks/T-005-institution-batch-department-management.md)  
Related schema: [user_db](../DATABASE_SCHEMA.md#user_db)

## Functional Requirements
- SPEC-005-FR-001 Super Admin users shall manage institutions and platform configuration.
- SPEC-005-FR-002 Institution Admin users shall manage departments inside their institution.
- SPEC-005-FR-003 Institution Admin users shall manage batches and cohorts inside their institution.
- SPEC-005-FR-004 Batch and department records shall support active, inactive, completed, suspended, or archived lifecycle states as applicable.
- SPEC-005-FR-005 Student and instructor profiles shall link to departments and batches where applicable.

## Non-Functional Requirements
- SPEC-005-NFR-001 Institution-scoped data access shall be enforced on the backend.
- SPEC-005-NFR-002 Lookup fields for institution, department, and batch shall be indexed.
- SPEC-005-NFR-003 Soft delete shall preserve historical relationships where business history is required.

## Acceptance Criteria
- SPEC-005-AC-001 Super Admin users can create and manage institutions.
- SPEC-005-AC-002 Institution Admin users cannot manage another institution.
- SPEC-005-AC-003 Batches and departments are searchable and filterable.
- SPEC-005-AC-004 Student enrollment workflows can reference batch or cohort identifiers.
