from pydantic import BaseModel

class AdminRouteItem(BaseModel):
  path: str
  name: str
  icon: str
  sequence: int
  requiredRoles: list[str]

class AdminRoutesList1(BaseModel):
  routes: list[AdminRouteItem]

class AdminRouteUpdate1(AdminRouteItem):
  pass

class AdminRouteDelete1(BaseModel):
  path: str
