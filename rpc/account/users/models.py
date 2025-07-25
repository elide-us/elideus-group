from pydantic import BaseModel
from datetime import datetime

class UserListItem(BaseModel):
  guid: str
  displayName: str

class AccountUsersList1(BaseModel):
  users: list[UserListItem]

class AccountUserRoles1(BaseModel):
  roles: list[str]

class AccountUserRolesUpdate1(BaseModel):
  userGuid: str
  roles: list[str]

class AccountUserCreditsUpdate1(BaseModel):
  userGuid: str
  credits: int

class AccountUserDisplayNameUpdate1(BaseModel):
  userGuid: str
  displayName: str

class AccountUserProfile1(BaseModel):
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
