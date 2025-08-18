from typing import Optional

from pydantic import BaseModel


class SystemRoutesRouteItem1(BaseModel):
  path: str
  name: str
  icon: Optional[str] = None
  sequence: int
  required_roles: list[str] = []


class SystemRoutesList1(BaseModel):
  routes: list[SystemRoutesRouteItem1]


class SystemRoutesDeleteRoute1(BaseModel):
  path: str
