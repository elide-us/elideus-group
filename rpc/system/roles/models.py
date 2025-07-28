from pydantic import BaseModel
from rpc.system.users.models import UserListItem

class RoleItem(BaseModel):
  name: str
  display: str
  bit: int

class SystemRolesList1(BaseModel):
  roles: list[RoleItem]

class SystemRoleUpdate1(BaseModel):
  name: str
  display: str
  bit: int

class SystemRoleDelete1(BaseModel):
  name: str

class SystemRoleMemberUpdate1(BaseModel):
  role: str
  userGuid: str

class SystemRoleMembers1(BaseModel):
  members: list['UserListItem']
  nonMembers: list['UserListItem']

class SystemRolesList2(BaseModel):
  roles: list[RoleItem]

class SystemRoleUpdate2(BaseModel):
  name: str
  display: str
  bit: int

class SystemRoleDelete2(BaseModel):
  name: str

class SystemRoleMemberUpdate2(BaseModel):
  role: str
  userGuid: str

class SystemRoleMembers2(BaseModel):
  members: list['UserListItem']
  nonMembers: list['UserListItem']
