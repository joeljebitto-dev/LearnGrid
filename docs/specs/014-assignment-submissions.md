# SPEC-014 Assignment Submissions

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-014](../tasks/T-014-assignment-submissions.md)  
Related schema: [assessment_db](../DATABASE_SCHEMA.md#assessment_db)

## Functional Requirements
- SPEC-014-FR-001 Students shall submit assignments.
- SPEC-014-FR-002 Assignment submissions may include text.
- SPEC-014-FR-003 Assignment submissions may include file uploads.
- SPEC-014-FR-004 Submissions shall be stored securely.
- SPEC-014-FR-005 Submission audit trails shall be preserved.
- SPEC-014-FR-006 AssignmentSubmitted events shall be published.

## Non-Functional Requirements
- SPEC-014-NFR-001 Assignment file uploads shall follow [SPEC-008](008-content-upload-storage-access.md).
- SPEC-014-NFR-002 Students shall be limited to their own submissions.
- SPEC-014-NFR-003 Instructors and Teaching Assistants shall be limited by course assignment permissions.

## Acceptance Criteria
- SPEC-014-AC-001 An enrolled student can submit an available assignment.
- SPEC-014-AC-002 Late submissions follow the assignment late-submission policy.
- SPEC-014-AC-003 Submission records retain audit metadata.
- SPEC-014-AC-004 Unauthorized users cannot view or alter submissions.
