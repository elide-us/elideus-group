from pydantic import BaseModel


class ServiceRolesRoles1(BaseModel):
  roles: list[str]


class ServiceRolesUpsertRole1(BaseModel):
  name: str
  bit: int
  display: str | None = None


class ServiceRolesDeleteRole1(BaseModel):
  name: str


class ServiceRolesRoleMemberUpdate1(BaseModel):
  role: str
  userGuid: str


class ServiceRolesUserItem1(BaseModel):
  guid: str
  displayName: str


class ServiceRolesRoleMembers1(BaseModel):
  members: list[ServiceRolesUserItem1]
  nonMembers: list[ServiceRolesUserItem1]
