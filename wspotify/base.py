import httpx

from wspotify.authorization import Scope
from wspotify.authorization.base import AuthorizationFlow
from wspotify.exceptions import IncompleteScopes, InvalidAuthorizationFlow


class APIReference:
    def __init__(self, authorization_flow: AuthorizationFlow) -> None:
        self.auth = authorization_flow
        self.base_url = "https://api.spotify.com/v1"
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {self.auth.access_token.access_token}"}
        )

    def check_access_token(self) -> None:
        """Check if the access token has expired or not. If expired,
        refresh the token."""
        if self.auth.access_token is None:
            raise
        if not self.auth.access_token.valid():
            self.auth.access_token = self.auth.refresh_access_token()
            self.client.headers["Authorization"] = (
                f"Bearer {self.auth.access_token.access_token}"
            )

    def check_scopes(self, required_scopes: list[Scope]) -> None:
        # Client credential flow has no authorization, therefore
        # it has no scopes
        if not hasattr(self.auth, "scopes"):
            raise InvalidAuthorizationFlow
        for scope in required_scopes:
            if scope not in self.auth.scopes:
                raise IncompleteScopes(required_scopes, self.auth.scopes)
