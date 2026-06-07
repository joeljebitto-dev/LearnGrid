from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .services import authenticate_access_token


class JWTAuthentication(BaseAuthentication):
    keyword = b"Bearer"

    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header:
            return None
        if len(header) != 2 or header[0] != self.keyword:
            raise AuthenticationFailed("Invalid authorization header.")

        token = header[1].decode("utf-8")
        account = authenticate_access_token(token)
        return (account, token)
