from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed


@dataclass(frozen=True)
class ServiceAccount:
    id: str
    token_payload: dict[str, Any]

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_active(self) -> bool:
        return True


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header:
            return None
        if len(header) != 2 or header[0].lower() != b"bearer":
            raise AuthenticationFailed("Invalid authorization header.")

        token = header[1].decode("utf-8")
        try:
            payload = jwt.decode(
                token,
                settings.AUTH_JWT_SIGNING_KEY,
                algorithms=[settings.AUTH_JWT_ALGORITHM],
                issuer=settings.AUTH_JWT_ISSUER,
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationFailed("Token has expired.") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthenticationFailed("Token is invalid.") from exc

        if payload.get("typ") != "access" or not payload.get("sub"):
            raise AuthenticationFailed("Token type is invalid.")
        return ServiceAccount(id=str(payload["sub"]), token_payload=payload), token
