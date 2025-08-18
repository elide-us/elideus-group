from pydantic import BaseModel


class SecurityRolesRoles1(BaseModel):
  roles: list[str]
