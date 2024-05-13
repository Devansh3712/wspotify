class AccessTokenError(Exception):
    def __init__(self, error: str):
        super().__init__(
            f"Unable to fetch access token due to the following reason: {error}"
        )


class AccessTokenNotFound(Exception):
    def __init__(self):
        super().__init__(
            "Access token not found, use an authorization flow to fetch one"
        )


class AuthorizationFailed(Exception):
    def __init__(self, error: str):
        super().__init__(
            f"User authorization failed due to the following reason: {error}"
        )


class InvalidState(Exception):
    def __init__(self):
        super().__init__(
            "State parsed from the redirect URI does not match the initial state"
        )


class StateNotFound(Exception):
    pass
