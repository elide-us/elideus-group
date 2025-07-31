from pydantic import BaseModel
from datetime import datetime

class AuthSessionTokens1(BaseModel):
  bearerToken: str
  rotationToken: str
  rotationExpires: datetime

class AccessToken1(BaseModel):
  accessSubject: str | None = None
  accessToken: str | None = None
  accessExpires: datetime | None = None

