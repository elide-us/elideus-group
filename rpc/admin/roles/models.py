from pydantic import BaseModel

class RoleItem(BaseModel):
  name: str
  bit: int

class AdminRolesList1(BaseModel):
  roles: list[RoleItem]

class AdminRoleUpdate1(BaseModel):
  name: str
  bit: int

class AdminRoleDelete1(BaseModel):
  name: str
