"""Content wiki query registry models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "CreateWikiParams",
  "CreateWikiVersionParams",
  "DeleteWikiParams",
  "GetWikiByRouteContextParams",
  "GetWikiBySlugParams",
  "GetWikiParams",
  "GetWikiVersionParams",
  "ListChildrenParams",
  "ListWikiParams",
  "ListWikiVersionsParams",
  "UpdateWikiParams",
  "WikiRecord",
  "WikiVersionRecord",
  "WikiWithContentRecord",
]


class ListWikiParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  parent_slug: str | None = None
  is_active: bool | None = None


class GetWikiParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class GetWikiBySlugParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  slug: str


class GetWikiByRouteContextParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  route_context: str


class ListChildrenParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  parent_slug: str


class CreateWikiParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  slug: str
  title: str
  content: str
  parent_slug: str | None = None
  route_context: str | None = None
  roles: int = 0
  sequence: int = 0
  created_by: str
  edit_summary: str | None = None


class UpdateWikiParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
  title: str | None = None
  parent_slug: str | None = None
  route_context: str | None = None
  roles: int | None = None
  is_active: bool | None = None
  sequence: int | None = None
  modified_by: str


class DeleteWikiParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
  modified_by: str


class CreateWikiVersionParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  wiki_recid: int
  content: str
  edit_summary: str | None = None
  created_by: str


class ListWikiVersionsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  wiki_recid: int


class GetWikiVersionParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int | None = None
  wiki_recid: int | None = None
  version: int | None = None


class WikiRecord(TypedDict):
  recid: int
  element_guid: str
  element_slug: str
  element_title: str
  element_parent_slug: str | None
  element_route_context: str | None
  element_roles: int
  element_is_active: bool
  element_sequence: int
  element_created_by: str
  element_modified_by: str
  element_created_on: str
  element_modified_on: str


class WikiWithContentRecord(WikiRecord, total=False):
  element_version: int | None
  element_content: str | None
  element_edit_summary: str | None
  version_created_by: str | None
  version_created_on: str | None


class WikiVersionRecord(TypedDict):
  recid: int
  wiki_recid: int
  element_version: int
  element_content: str
  element_edit_summary: str | None
  element_created_by: str
  element_created_on: str
