# Event Design Documents

These documents capture implemented asynchronous eventing design decisions for LearnGrid LMS.
They complement [BACKEND_ARCHITECTURE.md](../BACKEND_ARCHITECTURE.md), [SPEC-020](../specs/020-kafka-eventing.md), and [T-020](../tasks/T-020-kafka-eventing.md).

## Numbering
Event design documents use stable IDs:

- `EVT-020` for the Kafka eventing baseline.

## Implemented Designs
| ID | Design | Related task | Related spec |
| --- | --- | --- | --- |
| [EVT-020](EVT-020-kafka-eventing.md) | Kafka Eventing | [T-020](../tasks/T-020-kafka-eventing.md) | [SPEC-020](../specs/020-kafka-eventing.md) |

## Rules
- Keep event envelopes stable across services.
- Add new event topics only through the shared topic catalog.
- Consumers must be idempotent and must route poison messages to DLQ topics.
- Synchronous REST integrations remain the request-response source of truth unless a task explicitly changes that contract.
