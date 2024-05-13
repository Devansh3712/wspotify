import webbrowser
from base64 import urlsafe_b64encode
from urllib.parse import urlencode

import httpx

from wspotify.authorization.base import AuthorizationFlow
from wspotify.authorization.exceptions import (
    AccessTokenError,
    AccessTokenNotFound,
    InvalidState,
    StateNotFound,
)
from wspotify.authorization.schemas import AccessToken
from wspotify.authorization.scopes import Scope
from wspotify.authorization.utils import parse_code, parse_state


class AuthorizationCode(AuthorizationFlow):
    """The authorization code flow is suitable for long-running applications
    where the user grants permission only once.

    Attributes
    ----------
    client_id : str
    client_secret : str
    redirect_uri : str
    state : str or None, default=None
    scope : list[Scope], default=[]
    show_dialog : bool, default=False
    access_token : AccessToken or None, default=None

    References
    ----------
    .. [1] https://developer.spotify.com/documentation/web-api/tutorials/code-flow
    .. [2] https://developer.spotify.com/documentation/web-api/tutorials/refreshing-tokens
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        *,
        state: str | None = None,
        scopes: list[Scope] = [],
        show_dialog: bool = False,
    ) -> None:
        super().__init__(client_id)
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.state = state
        self.scopes = scopes
        self.show_dialog = show_dialog

    def get_authorization_url(self, *, open_in_browser: bool = False) -> str | None:
        """Request authorization from the user so that the app can access Spotify
        resources on the user's behalf.

        Parameters
        ----------
        open_in_browser : bool, default=False
            Open the authorization URL in the default browser

        Returns
        -------
        url : str
            Returns the authorization URL
        """
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "show_dialog": self.show_dialog,
        }
        if self.state:
            params["state"] = self.state
        if self.scopes:
            params["scope"] = " ".join(scope.value for scope in self.scopes)

        url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"
        if open_in_browser:
            webbrowser.open(url)
        else:
            return url

    def parse_redirect_uri(self, redirect_uri: str) -> str:
        """Parse the code and the state (if any) from the redirect URI.

        Parameters
        ----------
        redirect_uri : str
            The redirected URI after a user is authorized

        Returns
        -------
        code : str
            An authorization code that can be exchanged for an access
            token

        Raises
        ------
        InvalidState
            State mismatch from the redirected URI
        """
        try:
            code = parse_code(redirect_uri)
            state = parse_state(redirect_uri)
            if state != self.state:
                raise InvalidState
        except StateNotFound:
            pass
        return code

    def get_access_token(self, code: str) -> None:
        """Exchange the authorization code for an access token.

        Parameters
        ----------
        code : str
            Authorization code

        Raises
        ------
        AccessTokenError
            An error occured while fetching the access token
        """
        form = {
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
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

    def refresh_access_token(self, *, refresh_token: str | None = None) -> None:
        """Obtain new access token without requiring users to reauthorize
        the application.

        Parameters
        ----------
        refresh_token : str or None, default=None
            Refresh token returned after authorization flow

        Raises
        ------
        AccessTokenNotFound
            Access token has not been fetched
        AccessTokenError
            An error occured while fetching the access token
        """
        if self.access_token is None and refresh_token is None:
            raise AccessTokenNotFound
        if self.access_token and self.access_token.valid():
            return
        form = {
            "grant_type": "refresh_token",
            "refresh_token": (
                self.access_token.refresh_token
                if refresh_token is None
                else refresh_token
            ),
        }
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
