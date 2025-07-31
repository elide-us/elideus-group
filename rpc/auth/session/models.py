from datetime import datetime

from pydantic import BaseModel

class AccessToken1(BaseModel):
  accessToken: str
  accessSubject: str
  accessExpires: datetime
