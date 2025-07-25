from pydantic import BaseModel
from datetime import datetime

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
  backupEmail: str | None = None
  profilePicture: str | None = None
  credits: int | None = None
  storageUsed: int | None = None
  storageEnabled: bool | None = None
  displayEmail: bool = False
  rotationToken: str | None = None
  rotationExpires: datetime | None = None
