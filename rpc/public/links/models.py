from pydantic import BaseModel


class LinkItem(BaseModel):
  title: str
  url: str


class HomeLinks(BaseModel):
  links: list[LinkItem]


class NavbarRoute(BaseModel):
  path: str
  name: str
  icon: str | None = None


class NavbarRoutes(BaseModel):
  routes: list[NavbarRoute]

