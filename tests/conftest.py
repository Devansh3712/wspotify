import pytest
from pydantic_settings import BaseSettings, SettingsConfigDict

from wspotify.authorization import AuthorizationCode


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    SPOTIFY_CLIENT_ID: str
    SPOTIFY_CLIENT_SECRET: str
    SPOTIFY_REDIRECT_URI: str

    TEST_REFRESH_TOKEN: str


settings = Settings()


@pytest.fixture(scope="session")
def auth_flow():
    auth = AuthorizationCode(
        settings.SPOTIFY_CLIENT_ID,
        settings.SPOTIFY_CLIENT_SECRET,
        settings.SPOTIFY_REDIRECT_URI,
    )
    auth.refresh_access_token(refresh_token=settings.TEST_REFRESH_TOKEN)
    return auth
