from typing import Optional

from pydantic import BaseModel


class PublicLinksLinkItem1(BaseModel):
  title: str
  url: str


class PublicLinksHomeLinks1(BaseModel):
  links: list[PublicLinksLinkItem1]


class PublicLinksNavBarRoute1(BaseModel):
  path: str
  name: str
  icon: Optional[str] = None
  sequence: int


class PublicLinksNavBarRoutes1(BaseModel):
  routes: list[PublicLinksNavBarRoute1]

