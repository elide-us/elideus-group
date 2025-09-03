from pydantic import BaseModel


class AccountRoleRoleItem1(BaseModel):
  name: str
  mask: str
  display: str | None = None


class AccountRoleList1(BaseModel):
  roles: list[AccountRoleRoleItem1]


class AccountRoleMemberUpdate1(BaseModel):
  role: str
  userGuid: str


class AccountRoleUserItem1(BaseModel):
  guid: str
  displayName: str


class AccountRoleMembers1(BaseModel):
  members: list[AccountRoleUserItem1]
  nonMembers: list[AccountRoleUserItem1]


class AccountRoleUpsertRole1(BaseModel):
  name: str
  mask: str
  display: str | None = None


class AccountRoleDeleteRole1(BaseModel):
  name: str
