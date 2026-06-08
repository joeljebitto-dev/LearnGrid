# API-017 Notifications

Related task: [T-017](../tasks/T-017-notifications.md)  
Related spec: [SPEC-017](../specs/017-notifications.md)  
Related database design: [DBD-017](../db-design/DBD-017-notifications.md)

## API-017-001 Endpoints
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET/POST` | `/api/notifications/templates/` | List or upsert notification templates | `notification.view` or `notification.manage` |
| `GET/PATCH` | `/api/notifications/templates/<uuid>/` | Read or update one template | `notification.view` or `notification.manage` |
| `GET` | `/api/notifications/` | List current user's notifications, or scoped admin list | Owning profile or `notification.view` |
| `GET` | `/api/notifications/<uuid>/` | Read one notification | Owning profile or `notification.view` |
| `POST` | `/api/notifications/<uuid>/read/` | Mark one notification read | Owning profile or `notification.view` |
| `POST` | `/api/notifications/<uuid>/unread/` | Mark one notification unread | Owning profile or `notification.view` |
| `POST` | `/api/notifications/read-all/` | Mark current profile's unread notifications read | Owning profile |
| `GET/POST` | `/api/notifications/preferences/` | List or upsert current-user preferences; managers may target another profile | Owning profile or `notification.manage` |
| `GET` | `/api/notifications/delivery-attempts/` | List delivery attempts | `notification.view` |
| `GET` | `/api/notifications/delivery-attempts/<uuid>/` | Read one delivery attempt | `notification.view` |
| `POST` | `/api/notifications/events/ingest/` | Consume one notification event idempotently | `notification.manage` |

## API-017-002 Event Ingestion
Event ingestion accepts `event_id`, `event_type`, `aggregate_id`, optional `producer_service`, optional `timestamp`, and `payload`. Supported event types are `StudentEnrolled`, `AssignmentDueSoon`, `GradePublished`, and `CourseCompleted`.

Recipient resolution uses `payload.recipient_profile_ids` when present; otherwise it uses `payload.student_profile_id`. Responses include `status`, `notifications`, `skipped_count`, and `duplicate_count`.

## API-017-003 Behavior
The service creates in-app notifications with default persisted templates when no active template exists. `read_at` stores read state, `deleted_at` is reserved for soft delete, and delivery attempts store `sent` or `failed` in-app delivery status. Email, SMS, and push remain future delivery placeholders.
