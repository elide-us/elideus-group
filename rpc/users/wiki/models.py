from typing import Optional

from pydantic import BaseModel


class UsersWikiCreateVersion1(BaseModel):
  slug: str
  content: str
  edit_summary: Optional[str] = None


class UsersWikiCreatePage1(BaseModel):
  slug: str
  title: str
  content: str
  parent_slug: Optional[str] = None
  edit_summary: Optional[str] = None


class UsersWikiListVersions1(BaseModel):
  slug: str


class UsersWikiGetVersion1(BaseModel):
  slug: str
  version: int


class UsersWikiVersionItem1(BaseModel):
  recid: int
  element_version: int
  element_edit_summary: Optional[str] = None
  element_created_by: str
  element_created_on: Optional[str] = None


class UsersWikiVersionList1(BaseModel):
  versions: list[UsersWikiVersionItem1]


class UsersWikiVersionContent1(BaseModel):
  recid: int
  element_version: int
  element_content: str
  element_edit_summary: Optional[str] = None
  element_created_by: str
  element_created_on: Optional[str] = None
