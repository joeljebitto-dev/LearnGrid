from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
NGINX_CONFIG = ROOT / "infrastructure" / "docker" / "nginx" / "nginx.conf"
COMPOSE_NGINX_CONFIG = ROOT / "infrastructure" / "docker" / "nginx" / "compose.conf"
DOCKER_COMPOSE = ROOT / "docker-compose.yml"
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
APP_SERVICES = [*BACKEND_SERVICES, "frontend-service", "api-gateway"]


def test_nginx_config_documents_required_routes():
    config = NGINX_CONFIG.read_text(encoding="utf-8")

    required_prefixes = [
        "/api/auth/",
        "/api/users/",
        "/api/courses/",
        "/api/content/",
        "/api/enrollments/",
        "/api/progress/",
        "/api/assessments/",
        "/api/grading/",
        "/api/grades/",
        "/api/notifications/",
        "/api/analytics/",
        "/api/v1/",
    ]
    for prefix in required_prefixes:
        assert prefix in config


def test_nginx_config_has_gateway_controls():
    config = NGINX_CONFIG.read_text(encoding="utf-8")

    assert "listen 8443 ssl" in config
    assert "return 301 https://$host:8443$request_uri" in config
    assert "limit_req_zone" in config
    assert "client_max_body_size 20m" in config
    assert "Access-Control-Allow-Origin" in config
    assert 'default ""' in config
    assert 'add_header Vary "Origin" always' in config
    assert "Strict-Transport-Security" in config
    assert "X-Content-Type-Options" in config
    assert "X-Frame-Options" in config
    assert "Referrer-Policy" in config
    assert "Permissions-Policy" in config
    assert "Content-Security-Policy" in config
    assert "frame-ancestors 'none'" in config
    assert "learngrid_json" in config


def test_compose_nginx_config_uses_compose_service_dns():
    config = COMPOSE_NGINX_CONFIG.read_text(encoding="utf-8")

    assert "server frontend-service:5173;" in config
    for service in BACKEND_SERVICES:
        upstream_name = service.replace("-", "_")
        assert f"upstream {upstream_name}" in config
        assert f"server {service}:8000;" in config

    assert 'proxy_set_header Upgrade $http_upgrade' in config
    assert 'proxy_set_header Connection $connection_upgrade' in config
    assert "wss://127.0.0.1:*" in config
    assert "/api/v1/" in config


def test_compose_declares_full_app_stack_with_healthchecks():
    compose_config = yaml.safe_load(DOCKER_COMPOSE.read_text(encoding="utf-8"))
    services = compose_config["services"]

    for service in APP_SERVICES:
        assert service in services
        assert "healthcheck" in services[service]

    for service in BACKEND_SERVICES:
        assert "./scripts/sample-data:/app/scripts/sample-data:ro" in services[service]["volumes"]
        assert "./scripts/sample_data:/app/scripts/sample_data:ro" in services[service]["volumes"]

    assert services["api-gateway"]["volumes"][0].startswith(
        "./infrastructure/docker/nginx/compose.conf:"
    )
    assert services["api-gateway-host"]["profiles"] == ["host-dev"]
    assert services["api-gateway-host"]["volumes"][0].startswith(
        "./infrastructure/docker/nginx/nginx.conf:"
    )
    assert "gateway-cert" in services
