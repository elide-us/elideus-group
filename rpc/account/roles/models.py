from pydantic import BaseModel

################################################################################
## AccountRoleMember Operations

class AccountRoleMemberList1(BaseModel):
  guid: str
  displayName: str

class AccountRoleMemberUpdate1(BaseModel):
  role: str
  userGuid: str

class AccountRoleMembers1(BaseModel):
  members: list[AccountRoleMemberList1]
  nonMembers: list[AccountRoleMemberList1]

################################################################################
## AccountRole Operations

class AccountRoleItem1(BaseModel):
  name: str
  display: str
  bit: int

class AccountRolesList1(BaseModel):
  roles: list[AccountRoleItem1]

class AccountRoleUpdate1(BaseModel):
  name: str

class AccoutnRoleDelete1(BaseModel):
  name: str