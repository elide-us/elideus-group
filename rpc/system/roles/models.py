from pydantic import BaseModel


class SystemRolesRoleItem1(BaseModel):
  name: str
  mask: str
  display: str | None = None


class SystemRolesList1(BaseModel):
  roles: list[SystemRolesRoleItem1]


class SystemRolesUpsertRole1(BaseModel):
  name: str
  mask: str
  display: str | None = None


class SystemRolesDeleteRole1(BaseModel):
  name: str
