from pydantic import BaseModel


class ServiceRolesRoleItem1(BaseModel):
  name: str
  mask: str
  display: str | None = None


class ServiceRolesList1(BaseModel):
  roles: list[ServiceRolesRoleItem1]


class ServiceRolesUpsertRole1(BaseModel):
  name: str
  mask: str
  display: str | None = None


class ServiceRolesDeleteRole1(BaseModel):
  name: str
