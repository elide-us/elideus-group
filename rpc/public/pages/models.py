from typing import Optional

from pydantic import BaseModel, Field


class PublicPagesListFilter1(BaseModel):
  page_type: str | None = None


class PublicPagesGetPageRequest1(BaseModel):
  slug: str


class PublicPagesPageItem1(BaseModel):
  """Summary item for page listings."""

  slug: str
  title: str
  page_type: str
  category: Optional[str] = None
  is_pinned: bool = False
  sequence: int = 0
  element_created_on: Optional[str] = None
  element_modified_on: Optional[str] = None


class PublicPagesListPages1(BaseModel):
  """Response for list_pages."""

  pages: list[PublicPagesPageItem1]


class PublicPagesPermissions1(BaseModel):
  """Content access flags for the requesting user."""

  can_edit: bool = False
  can_delete: bool = False
  is_owner: bool = False


class PublicPagesGetPage1(BaseModel):
  """Response for get_page — includes content from latest version."""

  slug: str
  title: str
  page_type: str
  category: Optional[str] = None
  content: Optional[str] = None
  version: Optional[int] = None
  element_created_on: Optional[str] = None
  element_modified_on: Optional[str] = None
  permissions: PublicPagesPermissions1 = Field(default_factory=PublicPagesPermissions1)
