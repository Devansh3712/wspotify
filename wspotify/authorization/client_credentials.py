from base64 import urlsafe_b64encode

import httpx

from wspotify.authorization.base import AuthorizationFlow
from wspotify.authorization.exceptions import AccessTokenError
from wspotify.authorization.schemas import AccessToken


class ClientCredentials(AuthorizationFlow):
    """The client credentials flow is used in server-to-server authentication.
    Since this worflow does not include authorization, only endpoints that do
    not access user information can be accessed.

    Attributes
    ----------
    client_id : str
    client_secret : str
    access_token : AccessToken or None, default=None
    """

    def __init__(self, client_id: str, client_secret: str) -> None:
        super().__init__(client_id)
        self.client_secret = client_secret

    def get_access_token(self) -> None:
        """Fetch an access token

        Raises
        ------
        AccessTokenError
            An error occured while fetching the access token
        """
        form = {"grant_type": "client_credentials"}
        token = f"{self.client_id}:{self.client_secret}".encode()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {urlsafe_b64encode(token).decode()}",
        }

        response = httpx.post(self.token_url, headers=headers, data=form)
        data = response.json()
        if response.status_code != 200:
            error = data.get("error", None)
            raise AccessTokenError(error)
        self.access_token = AccessToken(**data)

    def refresh_access_token(self):
        # As this flow does not include authorization, no refresh token
        # is returned while requesting an access token. If the access
        # token expires, a new one will be requested using this method.
        self.get_access_token()
