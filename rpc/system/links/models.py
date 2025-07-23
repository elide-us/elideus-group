from pydantic import BaseModel

class LinkItem(BaseModel):
  title: str
  url: str

class SystemLinksHome1(BaseModel):
  links: list[LinkItem]

class RouteItem(BaseModel):
  path: str
  name: str
  icon: str

class SystemLinksRoutes1(BaseModel):
  routes: list[RouteItem]
