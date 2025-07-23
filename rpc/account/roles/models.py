from pydantic import BaseModel
from rpc.account.users.models import UserListItem

class RoleItem(BaseModel):
  name: str
  bit: int

class AccountRolesList1(BaseModel):
  roles: list[RoleItem]

class AccountRoleUpdate1(BaseModel):
  name: str
  bit: int

class AccountRoleDelete1(BaseModel):
  name: str

class AccountRoleMemberUpdate1(BaseModel):
  role: str
  userGuid: str

class AccountRoleMembers1(BaseModel):
  members: list[UserListItem]
  nonMembers: list[UserListItem]
