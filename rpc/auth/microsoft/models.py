from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuthMicrosoftLoginData1(BaseModel):
  bearerToken: str
  defaultProvider: str
  username: str
  email: str
  backupEmail: Optional[str] = None
  profilePicture: Optional[str] = None
  credits: Optional[int] = None

