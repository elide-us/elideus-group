from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FrontendUserProfileData1(BaseModel):
  bearerToken: str
  defaultProvider: str
  username: str
  email: str
  backupEmail: Optional[str] = None
  profilePicture: Optional[str] = None
  credits: Optional[int] = None
  storageUsed: Optional[int] = None
  storageEnabled: Optional[bool] = None
  displayEmail: bool = False
  roles: list[str] = []
  rotationToken: Optional[str] = None
  rotationExpires: Optional[datetime] = None

class FrontendUserSetDisplayName1(BaseModel):
  bearerToken: str
  displayName: str
