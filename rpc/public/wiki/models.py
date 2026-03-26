from typing import Optional

from pydantic import BaseModel, Field


class PublicWikiPageItem1(BaseModel):
  slug: str
  title: str
  parent_slug: Optional[str] = None
  sequence: int = 0
  element_created_on: Optional[str] = None
  element_modified_on: Optional[str] = None


class PublicWikiListPages1(BaseModel):
  pages: list[PublicWikiPageItem1]


class PublicWikiPermissions1(BaseModel):
  can_edit: bool = False
  can_delete: bool = False
  is_owner: bool = False


class PublicWikiGetPage1(BaseModel):
  slug: str
  title: str
  parent_slug: Optional[str] = None
  route_context: Optional[str] = None
  content: Optional[str] = None
  version: Optional[int] = None
  children: list[PublicWikiPageItem1] = Field(default_factory=list)
  element_created_on: Optional[str] = None
  element_modified_on: Optional[str] = None
  permissions: PublicWikiPermissions1 = Field(default_factory=PublicWikiPermissions1)
