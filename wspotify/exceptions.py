from wspotify.authorization import Scope


class IncompleteScopes(Exception):
    def __init__(self, expected: list[Scope], found: list[Scope]) -> None:
        missing: list[Scope] = [scope.name for scope in expected if scope not in found]
        super().__init__(
            f"Authorization flow is missing the following scopes: {missing}"
        )


class InvalidAuthorizationFlow(Exception):
    def __init__(self) -> None:
        super.__init__(
            "Invalid authorization flow, check documentation for choosing the correct flow"
        )


class ResponseError(Exception):
    def __init__(self, error: str) -> None:
        super().__init__(f"Got the following errror while fetching a response: {error}")
