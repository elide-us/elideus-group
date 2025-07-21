from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AuthMicrosoftLoginData1(BaseModel):
  bearerToken: str
  defaultProvider: str
  username: str
  email: str
  backupEmail: Optional[str] = None
  profilePicture: Optional[str] = None
  credits: Optional[int] = None
  rotationToken: Optional[str] = None
  rotationExpires: Optional[datetime] = None
