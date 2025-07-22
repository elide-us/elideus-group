from pydantic import BaseModel
from rpc.admin.users.models import UserListItem

class RoleItem(BaseModel):
  name: str
  bit: int

class AdminRolesList1(BaseModel):
  roles: list[RoleItem]

class AdminRoleUpdate1(BaseModel):
  name: str
  bit: int

class AdminRoleDelete1(BaseModel):
  name: str

class AdminRoleMemberUpdate1(BaseModel):
  role: str
  userGuid: str

class AdminRoleMembers1(BaseModel):
  members: list['UserListItem']
  nonMembers: list['UserListItem']
