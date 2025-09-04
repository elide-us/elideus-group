from typing import Optional

from pydantic import BaseModel


class ServiceRoutesRouteItem1(BaseModel):
  path: str
  name: str
  icon: Optional[str] = None
  sequence: int
  required_roles: list[str] = []


class ServiceRoutesList1(BaseModel):
  routes: list[ServiceRoutesRouteItem1]


class ServiceRoutesDeleteRoute1(BaseModel):
  path: str
