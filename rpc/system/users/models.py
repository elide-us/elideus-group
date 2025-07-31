from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserListItem(BaseModel):
  guid: str
  displayName: str

class SystemUsersList1(BaseModel):
  users: list[UserListItem]

class SystemUserRoles1(BaseModel):
  roles: list[str]

class SystemUserRolesUpdate1(BaseModel):
  userGuid: str
  roles: list[str]

class SystemUserCreditsUpdate1(BaseModel):
  userGuid: str
  credits: int

class SystemUserProfile1(BaseModel):
  guid: str
  defaultProvider: str
  username: str
  email: str
  backupEmail: Optional[str] = None
  profilePicture: Optional[str] = None
  credits: Optional[int] = 0
  storageUsed: Optional[int] = 0
  storageEnabled: bool = False
  displayEmail: bool = False
