from pydantic import BaseModel

class RoleMemberListItem1(BaseModel):
  guid: str
  displayName: str

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
  members: list['RoleMemberListItem1']
  nonMembers: list['RoleMemberListItem1']
