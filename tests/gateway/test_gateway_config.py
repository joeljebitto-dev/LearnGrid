from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NGINX_CONFIG = ROOT / "infrastructure" / "docker" / "nginx" / "nginx.conf"


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
