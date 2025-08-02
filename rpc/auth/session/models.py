from datetime import datetime

from pydantic import BaseModel


class AuthSessionBearerToken1(BaseModel):
  bearerToken: str
  bearerSubject: str
  bearerExpires: datetime

