# SPEC-017 Notifications

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-017](../tasks/T-017-notifications.md)  
Related schema: [notification_db](../DATABASE_SCHEMA.md#notification_db)

## Functional Requirements
- SPEC-017-FR-001 The system shall notify users about enrollment.
- SPEC-017-FR-002 The system shall notify users about assignment deadlines.
- SPEC-017-FR-003 The system shall notify users about grade publication.
- SPEC-017-FR-004 The system shall notify users about announcements.
- SPEC-017-FR-005 The system shall notify users about course completion.
- SPEC-017-FR-006 The system shall notify users about account-related events.
- SPEC-017-FR-007 In-app notifications shall be supported initially.
- SPEC-017-FR-008 Email, SMS, and push notifications shall be supported in future phases.
- SPEC-017-FR-009 Notification service shall consume Kafka events asynchronously.

## Non-Functional Requirements
- SPEC-017-NFR-001 Notification consumers shall be idempotent.
- SPEC-017-NFR-002 Delivery attempts shall preserve provider and failure metadata.
- SPEC-017-NFR-003 User preferences shall be respected where configured.

## Acceptance Criteria
- SPEC-017-AC-001 A StudentEnrolled event creates an in-app notification.
- SPEC-017-AC-002 A GradePublished event creates a student notification.
- SPEC-017-AC-003 Users can read and mark in-app notifications.
- SPEC-017-AC-004 Delivery failures are recorded without losing the notification.
