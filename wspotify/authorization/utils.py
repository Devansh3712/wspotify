import string
import secrets
from urllib.parse import urlparse, parse_qs

from wspotify.authorization.exceptions import (
    AuthorizationFailed,
    StateNotFound,
)


def generate_random_string(length: int) -> str:
    chars = string.ascii_letters + string.digits
    state_chars = [secrets.choice(chars) for _ in range(length)]
    state = "".join(state_chars)
    return state


def _parse_query_params(url: str) -> dict[str, list[str]]:
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    return query_params


def parse_code(redirect_uri: str) -> str:
    query_params = _parse_query_params(redirect_uri)
    code = query_params.get("code", None)
    if not code:
        error = query_params.get("error", None)
        raise AuthorizationFailed(error[0] if error else None)
    return code[0]


def parse_state(redirect_uri: str) -> str:
    query_params = _parse_query_params(redirect_uri)
    state = query_params.get("state", None)
    if not state:
        raise StateNotFound()
    return state[0]
