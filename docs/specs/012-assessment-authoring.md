# SPEC-012 Assessment Authoring

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-012](../tasks/T-012-assessment-authoring.md)  
Related schema: [assessment_db](../DATABASE_SCHEMA.md#assessment_db)

## Functional Requirements
- SPEC-012-FR-001 Instructors shall create quizzes.
- SPEC-012-FR-002 Instructors shall create question banks.
- SPEC-012-FR-003 Instructors shall create assignments.
- SPEC-012-FR-004 Instructors shall create exams.
- SPEC-012-FR-005 Question types shall include multiple choice, multiple select, true or false, short answer, essay, and file upload.
- SPEC-012-FR-006 Coding questions shall be supported in a future release.
- SPEC-012-FR-007 Assessment configuration shall support start and end windows.

## Non-Functional Requirements
- SPEC-012-NFR-001 Assessment authoring must enforce course-level instructor permissions.
- SPEC-012-NFR-002 Question bank queries shall be index-backed by institution, owner, and type.
- SPEC-012-NFR-003 Draft assessments shall not be visible to students.

## Acceptance Criteria
- SPEC-012-AC-001 A permitted instructor can create and update a question bank.
- SPEC-012-AC-002 A permitted instructor can create a draft quiz, exam, or assignment.
- SPEC-012-AC-003 Published assessment configuration is available to eligible enrolled students.
- SPEC-012-AC-004 Unauthorized authors cannot edit assessments outside their permitted scope.
