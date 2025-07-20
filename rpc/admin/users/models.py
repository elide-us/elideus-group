from pydantic import BaseModel

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
