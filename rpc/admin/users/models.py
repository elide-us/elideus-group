from pydantic import BaseModel
from datetime import datetime

class UserListItem(BaseModel):
  guid: str
  displayName: str

class AdminUsersList1(BaseModel):
  users: list[UserListItem]

class AdminUserRoles1(BaseModel):
  roles: list[str]

class AdminUserRolesUpdate1(BaseModel):
  userGuid: str
  roles: list[str]

class AdminUserCreditsUpdate1(BaseModel):
  userGuid: str
  credits: int

class AdminUserProfile1(BaseModel):
  guid: str
  defaultProvider: str
  username: str
  email: str
  backupEmail: str | None = None
  profilePicture: str | None = None
  credits: int | None = None
  storageUsed: int | None = None
  displayEmail: bool = False
  rotationToken: str | None = None
  rotationExpires: datetime | None = None
