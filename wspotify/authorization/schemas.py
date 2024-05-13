from datetime import datetime, timedelta

from pydantic import BaseModel


class AccessToken(BaseModel):
    access_token: str
    token_type: str
    scope: str | None = None
    created_at: datetime = datetime.now()
    expires_in: int
    refresh_token: str | None = None

    def valid(self) -> bool:
        now = datetime.now()
        if now > self.created_at + timedelta(seconds=self.expires_in):
            return False
        return True
