from pydantic import BaseModel
from rpc.account.users.models import UserListItem

class RoleItem(BaseModel):
  name: str
  display: str
  bit: int

class AccountRolesList1(BaseModel):
  roles: list[RoleItem]

class AccountRoleUpdate1(BaseModel):
  name: str
  display: str
  bit: int

class AccountRoleDelete1(BaseModel):
  name: str

class AccountRoleMemberUpdate1(BaseModel):
  role: str
  userGuid: str

class AccountRoleMembers1(BaseModel):
  members: list[UserListItem]
  nonMembers: list[UserListItem]

class AccountRolesList2(BaseModel):
  roles: list[RoleItem]

class AccountRoleUpdate2(BaseModel):
  name: str
  display: str
  bit: int

class AccountRoleDelete2(BaseModel):
  name: str

class AccountRoleMemberUpdate2(BaseModel):
  role: str
  userGuid: str

class AccountRoleMembers2(BaseModel):
  members: list[UserListItem]
  nonMembers: list[UserListItem]
