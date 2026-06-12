# T-024 Testing And Quality

Related spec: [SPEC-024](../specs/024-testing-quality.md)  
Related doc: [TESTING_STRATEGY.md](../TESTING_STRATEGY.md)

- [x] T-024.01 Add unit tests for models, services, selectors, permissions, and serializers.
- [x] T-024.02 Add API tests for authentication, permissions, validation, happy paths, and failure paths.
- [x] T-024.03 Add integration tests for PostgreSQL, Redis, Kafka, and object storage.
- [x] T-024.04 Add contract tests for service APIs and Kafka event schemas.
- [x] T-024.05 Add Selenium page objects and E2E tests for main user journeys.
- [x] T-024.06 Add load tests for login, dashboard, course listing, lesson access, quiz submission, and notifications.
- [x] T-024.07 Add formatting, linting, type checking, and security checks to CI.
- [ ] T-024.08 Verify p95 latency, error rate, throughput, PostgreSQL connections, Redis memory, Kafka lag, CPU, memory, and autoscaling behavior before production.
  Remains open until a real staging/on-prem Kubernetes run proves the performance, resource, Kafka
  lag, and autoscaling thresholds.
