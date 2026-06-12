import os
import ssl
from urllib import error, request

import pytest


def gateway_url(path: str = "") -> str:
    base_url = os.getenv("GATEWAY_BASE_URL")
    if not base_url:
        pytest.skip("Set GATEWAY_BASE_URL to run live gateway smoke tests.")
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def open_gateway(path: str, *, method: str = "GET", data: bytes | None = None, headers=None):
    req = request.Request(gateway_url(path), data=data, headers=headers or {}, method=method)
    return request.urlopen(req, context=ssl._create_unverified_context(), timeout=5)


def test_gateway_health_live():
    with open_gateway("/gateway/health") as response:
        assert response.status == 200
        assert b'"service":"api-gateway"' in response.read()


def test_gateway_cors_preflight_live():
    with open_gateway(
        "/api/auth/session/",
        method="OPTIONS",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    ) as response:
        assert response.status == 204
        assert response.headers["Access-Control-Allow-Origin"] == "http://127.0.0.1:5173"
        assert response.headers["Vary"] == "Origin"


def test_gateway_disallowed_cors_origin_live():
    with open_gateway(
        "/api/auth/session/",
        method="OPTIONS",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    ) as response:
        assert response.status == 204
        assert response.headers.get("Access-Control-Allow-Origin", "") == ""


def test_gateway_security_headers_live():
    with open_gateway("/gateway/health") as response:
        assert response.headers["Strict-Transport-Security"].startswith("max-age=31536000")
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_gateway_oversized_request_live():
    payload = b"x" * (21 * 1024 * 1024)
    with pytest.raises(error.HTTPError) as exc_info:
        open_gateway(
            "/api/auth/token/issue/",
            method="POST",
            data=payload,
            headers={"Content-Type": "application/json"},
        )

    assert exc_info.value.code == 413


def test_gateway_http_redirect_live():
    http_base_url = os.getenv("GATEWAY_HTTP_URL")
    if not http_base_url:
        pytest.skip("Set GATEWAY_HTTP_URL to run HTTP redirect smoke test.")

    class NoRedirect(request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = request.build_opener(NoRedirect)
    req = request.Request(f"{http_base_url.rstrip('/')}/gateway/health", method="GET")
    try:
        opener.open(req, timeout=5)
    except error.HTTPError as exc:
        assert exc.code in {301, 308}
        assert exc.headers["Location"].startswith("https://")
