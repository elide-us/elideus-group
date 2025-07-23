from pydantic import BaseModel

class LinkItem(BaseModel):
  title: str
  url: str

class FrontendLinksHome1(BaseModel):
  links: list[LinkItem]

class RouteItem(BaseModel):
  path: str
  name: str
  icon: str

class FrontendLinksRoutes1(BaseModel):
  routes: list[RouteItem]
