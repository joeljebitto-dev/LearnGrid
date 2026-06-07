# API-010 Learning Progress Tracking

Related task: [T-010](../tasks/T-010-learning-progress-tracking.md)  
Related spec: [SPEC-010](../specs/010-learning-progress-tracking.md)  
Related database design: [DBD-010](../db-design/DBD-010-learning-progress-tracking.md)

## API-010-001 Endpoints
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `POST` | `/api/progress/lessons/` | Upsert lesson progress | `progress.manage` |
| `POST` | `/api/progress/videos/` | Upsert video progress | `progress.manage` |
| `POST` | `/api/progress/assessments/` | Upsert assessment progress | `progress.manage` |
| `GET` | `/api/progress/courses/` | List course progress summaries | `progress.view` |
| `GET` | `/api/progress/courses/<uuid>/` | Read one course progress summary | `progress.view` |
| `GET/POST` | `/api/progress/events/` | List or ingest progress events | `progress.view/manage` |

## API-010-002 Notes
Update payloads include student/course IDs plus the target lesson, content asset, or assessment ID. Optional `total_lessons` and `total_assessments` let callers provide a course denominator until course-service aggregate reads are integrated.
