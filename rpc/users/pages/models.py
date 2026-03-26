from typing import Optional

from pydantic import BaseModel


class UsersPagesCreateVersion1(BaseModel):
  slug: str
  content: str
  summary: Optional[str] = None


class UsersPagesListVersions1(BaseModel):
  slug: str


class UsersPagesGetVersion1(BaseModel):
  slug: str
  version: int


class UsersPagesVersionItem1(BaseModel):
  recid: int
  element_version: int
  element_summary: Optional[str] = None
  element_created_by: str
  element_created_on: Optional[str] = None


class UsersPagesVersionList1(BaseModel):
  versions: list[UsersPagesVersionItem1]


class UsersPagesVersionContent1(BaseModel):
  recid: int
  element_version: int
  element_content: str
  element_summary: Optional[str] = None
  element_created_by: str
  element_created_on: Optional[str] = None
