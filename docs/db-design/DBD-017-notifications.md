# DBD-017 Notifications

Related task: [T-017](../tasks/T-017-notifications.md)  
Related spec: [SPEC-017](../specs/017-notifications.md)  
Canonical schema: [notification_db](../DATABASE_SCHEMA.md#notification_db)

## DBD-017-001 Scope
`notification-service` now owns in-app notification templates, notification records, delivery attempts, and user notification preferences. Kafka transport remains future [T-020](../tasks/T-020-kafka-eventing.md) scope; T-017 exposes an authenticated event-ingest API with idempotent processing.

## DBD-017-002 Tables
| Table ID | Table | Purpose |
| --- | --- | --- |
| `DB-NOTIFY-001` | `notification_templates` | Event/channel templates for in-app and future channels |
| `DB-NOTIFY-002` | `notifications` | In-app user notification records and read state |
| `DB-NOTIFY-003` | `delivery_attempts` | In-app delivery status and failure metadata |
| `DB-NOTIFY-004` | `user_notification_preferences` | Per-profile event/channel preference flags |

## DBD-017-003 Relationships And Constraints
- `delivery_attempts.notification_id` is an in-service foreign key to `notifications.id`.
- `notification_templates` is unique by `event_type` and `channel`.
- `user_notification_preferences` is unique by `profile_id`, `event_type`, and `channel`.
- `recipient_profile_id` and `profile_id` are cross-service UUID references to user-service.

## DBD-017-004 Behavior Notes
- Ingested event IDs are stored in `notifications.payload.source_event_id` and checked with recipient/event type for idempotency.
- Disabled in-app preferences skip notification creation.
- Delivery failures create `delivery_attempts` rows without dropping the notification.
- Email, SMS, and push are accepted as future channel values in templates and preferences but delivery is not implemented in T-017.
