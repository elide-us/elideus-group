
from pydantic import BaseModel


class LinkItem(BaseModel):
  title: str
  url: str


class AdminLinksHome1(BaseModel):
  links: list[LinkItem]


class RouteItem(BaseModel):
  path: str
  name: str
  icon: str

class AdminLinksRoutes1(BaseModel):
  routes: list[RouteItem]
