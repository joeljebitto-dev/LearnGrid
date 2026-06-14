from __future__ import annotations

import json
from types import SimpleNamespace
from urllib import error

import pytest
from django.conf import settings


if not settings.configured:
    settings.configure(
        AUTH_SERVICE_BASE_URL="http://auth-service",
        AUTHORIZATION_CHECK_TIMEOUT_SECONDS=2,
        DEFAULT_CHARSET="utf-8",
        SECRET_KEY="test",
        INSTALLED_APPS=[],
    )

from rest_framework.exceptions import PermissionDenied  # noqa: E402

from learngrid_authz import (  # noqa: E402
    RemoteAuthorizationPermission,
    authorization_timeout_seconds,
    remote_authorization_check,
    require_remote_permission,
)
from learngrid_authz import client  # noqa: E402


class FakeResponse:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_remote_authorization_check_allows_success(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["authorization"] = request.headers["Authorization"]
        return FakeResponse({"allowed": True})

    monkeypatch.setattr(client.urlrequest, "urlopen", fake_urlopen)

    assert remote_authorization_check(
        token="access-token",
        permission="course.view",
        scope_type="institution",
        scope_id="inst-1",
    )
    assert captured == {
        "url": "http://auth-service/api/auth/authorization/check/",
        "timeout": 2.0,
        "body": {
            "permission": "course.view",
            "scope_type": "institution",
            "scope_id": "inst-1",
        },
        "authorization": "Bearer access-token",
    }


def test_remote_authorization_check_denies_network_errors(monkeypatch):
    def fake_urlopen(_request, timeout):
        raise error.URLError("down")

    monkeypatch.setattr(client.urlrequest, "urlopen", fake_urlopen)

    assert not remote_authorization_check(token="access-token", permission="course.view")


def test_remote_authorization_check_denies_missing_inputs():
    assert not remote_authorization_check(token=None, permission="course.view")
    assert not remote_authorization_check(token="access-token", permission=None)


def test_require_remote_permission_raises_on_denial(monkeypatch):
    monkeypatch.setattr(client, "remote_authorization_check", lambda **_kwargs: False)

    with pytest.raises(PermissionDenied):
        require_remote_permission(token="access-token", permission="course.manage")


def test_authorization_timeout_uses_default_for_invalid_setting(monkeypatch):
    monkeypatch.setattr(settings, "AUTHORIZATION_CHECK_TIMEOUT_SECONDS", "invalid", raising=False)

    assert authorization_timeout_seconds(default=3.5) == 3.5


def test_remote_authorization_permission_resolves_scope_from_request_data(monkeypatch):
    monkeypatch.setattr(
        client, "remote_authorization_check", lambda **kwargs: kwargs["scope_id"] == "inst-1"
    )
    permission = RemoteAuthorizationPermission()
    view = SimpleNamespace(required_permission="profile.view", required_scope_type="institution")
    request = SimpleNamespace(
        user=SimpleNamespace(is_authenticated=True),
        auth="access-token",
        data={"institution_id": "inst-1"},
        query_params={},
        parser_context={},
    )

    assert permission.has_permission(request, view)
