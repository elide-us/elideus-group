from datetime import datetime

from pydantic import BaseModel


class AuthSessionTokens1(BaseModel):
  bearerToken: str

class AccessToken1(BaseModel):
  accessSubject: str | None = None
  accessToken: str | None = None
  accessExpires: datetime | None = None


