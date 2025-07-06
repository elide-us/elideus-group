
from pydantic import BaseModel


class LinkItem(BaseModel):
  title: str
  url: str


class AdminLinksHome1(BaseModel):
  links: list[LinkItem]

