from datetime import datetime

from pydantic import BaseModel


class AuthSessionTokens1(BaseModel):
  bearerToken: str


class AccessToken1(BaseModel):
  accessToken: str
  accessSubject: str
  accessExpires: datetime
