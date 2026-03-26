from typing import Optional

from pydantic import BaseModel


class ServicePagesPageItem1(BaseModel):
  recid: int
  slug: str
  title: str
  page_type: str
  category: Optional[str] = None
  roles: int = 0
  is_active: bool = True
  is_pinned: bool = False
  sequence: int = 0
  element_created_on: Optional[str] = None
  element_modified_on: Optional[str] = None


class ServicePagesListPages1(BaseModel):
  pages: list[ServicePagesPageItem1]


class ServicePagesCreatePage1(BaseModel):
  slug: str
  title: str
  content: str
  page_type: str = "article"
  category: Optional[str] = None
  roles: int = 0
  is_pinned: bool = False
  sequence: int = 0
  summary: Optional[str] = None


class ServicePagesUpdatePage1(BaseModel):
  recid: int
  title: Optional[str] = None
  page_type: Optional[str] = None
  category: Optional[str] = None
  roles: Optional[int] = None
  is_active: Optional[bool] = None
  is_pinned: Optional[bool] = None
  sequence: Optional[int] = None


class ServicePagesDeletePage1(BaseModel):
  recid: int
