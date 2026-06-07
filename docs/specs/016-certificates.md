# SPEC-016 Certificates

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-016](../tasks/T-016-certificates.md)  
Related schema: [grading_db](../DATABASE_SCHEMA.md#grading_db)

## Functional Requirements
- SPEC-016-FR-001 The system shall support future course completion certificates.
- SPEC-016-FR-002 Certificate eligibility shall be calculated from course completion and grade rules.
- SPEC-016-FR-003 Certificate eligibility shall emit CertificateEligible events where applicable.
- SPEC-016-FR-004 Issued certificates shall have unique certificate numbers.
- SPEC-016-FR-005 Certificates may reference generated content assets.

## Non-Functional Requirements
- SPEC-016-NFR-001 Certificate decisions shall preserve eligibility audit data.
- SPEC-016-NFR-002 Certificate records shall remain available after course completion.
- SPEC-016-NFR-003 Revoked certificates shall retain revocation timestamps.

## Acceptance Criteria
- SPEC-016-AC-001 Eligible students can receive certificate eligibility records.
- SPEC-016-AC-002 Issued certificate numbers are unique.
- SPEC-016-AC-003 Revoked certificates are not presented as valid.
