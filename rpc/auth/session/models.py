from pydantic import BaseModel
from datetime import datetime

class AuthSessionTokens1(BaseModel):
  bearerToken: str
  rotationToken: str
  rotationExpires: datetime
