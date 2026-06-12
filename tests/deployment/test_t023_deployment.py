from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND_SERVICES = [
    "auth-service",
    "user-service",
    "course-service",
    "content-service",
    "enrollment-service",
    "progress-service",
    "assessment-service",
    "grading-service",
    "notification-service",
    "analytics-service",
]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_backend_dockerfiles_exist_and_run_gunicorn():
    for service in BACKEND_SERVICES:
        dockerfile = ROOT / "backend" / "services" / service / "Dockerfile"
        assert dockerfile.exists(), service
        contents = dockerfile.read_text(encoding="utf-8")
        assert f"ARG SERVICE_NAME={service}" in contents
        assert "gunicorn config.wsgi:application" in contents
        assert "USER learngrid" in contents


def test_frontend_and_gateway_images_have_health_endpoints():
    assert "location = /healthz" in read("frontend/nginx.conf")
    assert "VITE_API_BASE_URL=/api" in read("frontend/Dockerfile")
    assert "location = /gateway/health" in read("infrastructure/docker/nginx/kubernetes.conf")
    assert "frontend-service:8080" in read("infrastructure/docker/nginx/kubernetes.conf")


def test_app_chart_contains_required_workload_primitives():
    chart = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "infrastructure" / "helm" / "learngrid-app" / "templates").glob("*.yaml")
    )
    for kind in [
        "kind: Deployment",
        "kind: Service",
        "kind: ConfigMap",
        "kind: Secret",
        "kind: HorizontalPodAutoscaler",
        "kind: Job",
        "kind: PodDisruptionBudget",
        "kind: NetworkPolicy",
    ]:
        assert kind in chart
    assert "/health/live/" in chart
    assert "/health/ready/" in chart
    assert "readOnlyRootFilesystem: true" in chart


def test_runtime_chart_contains_required_observability_stack():
    chart = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "infrastructure" / "helm" / "learngrid-runtime" / "templates").glob("*.yaml")
    )
    for token in [
        "kind: Cluster",
        "kind: ScheduledBackup",
        "kind: Kafka",
        "kind: Tenant",
        "name: prometheus",
        "name: grafana",
        "name: loki",
        "name: tempo",
        "name: alloy",
        "name: postgres-exporter",
        "name: redis-exporter",
        "name: kafka-exporter",
        "name: kafka-ui",
    ]:
        assert token in chart
    assert "barmanObjectStore" in chart


def test_grafana_dashboards_are_valid_json_and_cover_required_views():
    dashboard_dir = ROOT / "infrastructure" / "helm" / "learngrid-runtime" / "dashboards"
    dashboards = {}
    for path in dashboard_dir.glob("*.json"):
        dashboards[path.name] = json.loads(path.read_text(encoding="utf-8"))

    assert dashboards
    titles = " ".join(dashboard["title"] for dashboard in dashboards.values())
    for expected in ["API", "Kafka", "PostgreSQL", "Redis", "User Activity", "Assessments"]:
        assert expected in titles or any(
            expected in panel.get("title", "")
            for dashboard in dashboards.values()
            for panel in dashboard.get("panels", [])
        )


def test_ci_cd_workflow_contains_image_scan_push_and_deploy_gates():
    workflow = read(".github/workflows/ci.yml")
    for token in [
        "Build And Scan Images",
        "aquasecurity/trivy-action",
        "ghcr.io",
        "helm lint",
        "kubeconform",
        "Deploy Staging",
        "KUBE_CONFIG_STAGING",
        "environment: production",
        "KUBE_CONFIG_PRODUCTION",
        "tests/e2e",
    ]:
        assert token in workflow
