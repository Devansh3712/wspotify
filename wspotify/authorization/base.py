from abc import ABC, abstractmethod

from wspotify.authorization.schemas import AccessToken


class AuthorizationFlow(ABC):
    """Abstract class for authorization flows to request and get
    an access token.

    Attributes
    ----------
    client_id : str
    access_token : AccessToken or None, default=None
    token_url : str
    """

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.access_token: AccessToken | None = None
        self.token_url = "https://accounts.spotify.com/api/token"

    @abstractmethod
    def get_access_token(self) -> None:
        pass

    @abstractmethod
    def refresh_access_token(self) -> None:
        pass
