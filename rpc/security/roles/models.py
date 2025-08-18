from pydantic import BaseModel


class SecurityRolesRoles1(BaseModel):
  roles: list[str]


class SecurityRolesUpsertRole1(BaseModel):
  name: str
  bit: int
  display: str | None = None


class SecurityRolesDeleteRole1(BaseModel):
  name: str


class SecurityRolesRoleMemberUpdate1(BaseModel):
  role: str
  userGuid: str


class SecurityRolesUserItem1(BaseModel):
  guid: str
  displayName: str


class SecurityRolesRoleMembers1(BaseModel):
  members: list[SecurityRolesUserItem1]
  nonMembers: list[SecurityRolesUserItem1]
