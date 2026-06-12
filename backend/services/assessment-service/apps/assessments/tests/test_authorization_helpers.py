import json
from datetime import timedelta
from urllib import error
from uuid import uuid4

import jwt
import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from apps.assessments import permissions
from apps.assessments.authentication import JWTAuthentication


def make_token(*, seconds=300, token_type="access"):
    now = timezone.now()
    payload = {
        "iss": settings.AUTH_JWT_ISSUER,
        "sub": str(uuid4()),
        "typ": token_type,
        "jti": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=seconds)).timestamp()),
    }
    return jwt.encode(payload, settings.AUTH_JWT_SIGNING_KEY, algorithm=settings.AUTH_JWT_ALGORITHM)


def authenticated_request(factory, token):
    request = factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")
    user, raw_token = JWTAuthentication().authenticate(request)
    request.user = user
    request.auth = raw_token
    return request


class FakeResponse:
    status = 200

    def __init__(self, allowed):
        self.allowed = allowed

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _traceback):
        return None

    def read(self):
        return json.dumps({"allowed": self.allowed}).encode("utf-8")


class CourseView:
    required_permission = "course.view"
    required_scope_type = "course"

    def __init__(self, course_id):
        self.kwargs = {"course_id": str(course_id)}


@pytest.fixture
def api_factory():
    return APIRequestFactory()


def test_jwt_authentication_accepts_valid_access_token(api_factory):
    token = make_token()
    user, raw_token = JWTAuthentication().authenticate(
        api_factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")
    )

    assert user.is_authenticated
    assert raw_token == token


def test_jwt_authentication_rejects_malformed_and_expired_tokens(api_factory):
    with pytest.raises(AuthenticationFailed):
        JWTAuthentication().authenticate(
            api_factory.get("/", HTTP_AUTHORIZATION="Bearer not-a-jwt")
        )

    with pytest.raises(AuthenticationFailed):
        JWTAuthentication().authenticate(
            api_factory.get("/", HTTP_AUTHORIZATION=f"Bearer {make_token(seconds=-1)}")
        )


def test_remote_permission_allows_authorized_response(monkeypatch, api_factory):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["authorization"] = request.headers["Authorization"]
        return FakeResponse(True)

    monkeypatch.setattr(permissions.urlrequest, "urlopen", fake_urlopen)
    token = make_token()
    course_id = uuid4()
    request = authenticated_request(api_factory, token)

    allowed = permissions.RemoteAuthorizationPermission().has_permission(
        request,
        CourseView(course_id),
    )

    assert allowed
    assert captured["timeout"] == 2
    assert captured["payload"] == {
        "permission": "course.view",
        "scope_type": "course",
        "scope_id": str(course_id),
    }
    assert captured["authorization"] == f"Bearer {token}"


def test_remote_permission_denies_unauthorized_and_network_failure(monkeypatch, api_factory):
    token = make_token()
    request = authenticated_request(api_factory, token)
    permission = permissions.RemoteAuthorizationPermission()

    monkeypatch.setattr(
        permissions.urlrequest, "urlopen", lambda _request, timeout: FakeResponse(False)
    )
    assert not permission.has_permission(request, CourseView(uuid4()))

    def broken_urlopen(_request, timeout):
        raise error.URLError("auth-service unavailable")

    monkeypatch.setattr(permissions.urlrequest, "urlopen", broken_urlopen)
    assert not permission.has_permission(request, CourseView(uuid4()))
