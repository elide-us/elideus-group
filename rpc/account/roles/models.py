from pydantic import BaseModel

class AccountRoleMemberList1(BaseModel):
  guid: str
  displayName: str

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
  members: list[AccountRoleMemberList1]
  nonMembers: list[AccountRoleMemberList1]
