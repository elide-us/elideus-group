from pydantic import BaseModel

class SystemRouteItem(BaseModel):
  path: str
  name: str
  icon: str
  sequence: int
  requiredRoles: list[str]

class SystemRoutesList1(BaseModel):
  routes: list[SystemRouteItem]

class SystemRouteUpdate1(SystemRouteItem):
  pass

class SystemRouteDelete1(BaseModel):
  path: str
