# Testing Strategy

Source: [SRD.pdf](SRD.pdf)

## TEST-001 Scope
Testing covers unit, API, integration, contract, browser end-to-end, load, security, and deployment smoke tests.

## TEST-002 Unit Tests
- Test models, services, selectors, permissions, and serializers.
- Test business logic independently from API views where possible.
- Use Pytest and Django Test Framework.

## TEST-003 API Tests
- Cover authentication, permissions, validation, happy paths, and failure paths.
- Include object-level authorization tests for protected resources.
- Include pagination, filtering, and sorting tests for list endpoints.

## TEST-004 Integration Tests
- Verify PostgreSQL migrations and service-level transactions.
- Verify Redis caching, rate limiting, OTPs, token blacklist, and locks.
- Verify Kafka producers, consumers, retries, dead-letter paths, idempotency, and lag reporting through the shared `learngrid-events` package.
- Verify object storage upload, signed access, metadata, and permission behavior.
- Use Testcontainers where suitable in CI.

## TEST-005 Selenium E2E Tests
Required journeys:
- Student login
- Instructor login
- Admin login
- Course creation
- Course publishing
- Student enrollment
- Lesson viewing
- Quiz attempt
- Assignment submission
- Grade viewing
- Role-based access control
- Logout

Suggested structure:

```text
tests/e2e/pages/login_page.py
tests/e2e/pages/dashboard_page.py
tests/e2e/pages/course_page.py
tests/e2e/pages/assessment_page.py
tests/e2e/tests/test_login.py
tests/e2e/tests/test_course_enrollment.py
tests/e2e/tests/test_lesson_completion.py
tests/e2e/tests/test_quiz_submission.py
```

## TEST-006 Load Tests
- Simulate login, dashboard loading, course listing, lesson access, quiz submission, and notifications.
- Use k6, Locust, or JMeter.
- Track p95 latency, error rate, throughput, PostgreSQL connections, Redis memory, Kafka lag, CPU, memory, and autoscaling behavior.
- Common API requests target p95 latency below 300 ms under normal load, excluding large file downloads and video streaming.

## TEST-007 Related Spec And Task
Primary spec: [SPEC-024](specs/024-testing-quality.md).  
Primary task: [T-024](tasks/T-024-testing-quality.md).
