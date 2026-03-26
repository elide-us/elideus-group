"""Content pages query registry models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "CreatePageParams",
  "CreateVersionParams",
  "DeletePageParams",
  "GetPageBySlugParams",
  "GetPageParams",
  "GetVersionParams",
  "ListPagesParams",
  "ListVersionsParams",
  "PageRecord",
  "PageWithContentRecord",
  "UpdatePageParams",
  "VersionRecord",
]


class ListPagesParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  page_type: str | None = None
  is_active: bool | None = None


class GetPageParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class GetPageBySlugParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  slug: str


class CreatePageParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  slug: str
  title: str
  content: str
  page_type: str = "article"
  category: str | None = None
  roles: int = 0
  is_pinned: bool = False
  sequence: int = 0
  created_by: str
  summary: str | None = None


class UpdatePageParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
  title: str | None = None
  page_type: str | None = None
  category: str | None = None
  roles: int | None = None
  is_active: bool | None = None
  is_pinned: bool | None = None
  sequence: int | None = None
  modified_by: str


class DeletePageParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
  modified_by: str


class CreateVersionParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  pages_recid: int
  content: str
  summary: str | None = None
  created_by: str


class ListVersionsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  pages_recid: int


class GetVersionParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int | None = None
  pages_recid: int | None = None
  version: int | None = None


class PageRecord(TypedDict):
  recid: int
  element_guid: str
  element_slug: str
  element_title: str
  element_page_type: str
  element_category: str | None
  element_roles: int
  element_is_active: bool
  element_is_pinned: bool
  element_sequence: int
  element_created_by: str
  element_modified_by: str
  element_created_on: str
  element_modified_on: str


class PageWithContentRecord(PageRecord, total=False):
  element_version: int | None
  element_content: str | None
  element_summary: str | None
  version_created_by: str | None
  version_created_on: str | None


class VersionRecord(TypedDict):
  recid: int
  pages_recid: int
  element_version: int
  element_content: str
  element_summary: str | None
  element_created_by: str
  element_created_on: str
