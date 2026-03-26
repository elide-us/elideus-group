"""Content wiki query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  CreateWikiParams,
  CreateWikiVersionParams,
  DeleteWikiParams,
  GetWikiByRouteContextParams,
  GetWikiBySlugParams,
  GetWikiParams,
  GetWikiVersionParams,
  ListChildrenParams,
  ListWikiParams,
  ListWikiVersionsParams,
  UpdateWikiParams,
)

__all__ = [
  "create_version_request",
  "create_wiki_request",
  "delete_wiki_request",
  "get_version_request",
  "get_wiki_by_route_context_request",
  "get_wiki_by_slug_request",
  "get_wiki_request",
  "list_children_request",
  "list_versions_request",
  "list_wiki_request",
  "update_wiki_request",
]


def list_wiki_request(params: ListWikiParams) -> DBRequest:
  return DBRequest(op="db:content:wiki:list:1", payload=params.model_dump())


def get_wiki_request(params: GetWikiParams) -> DBRequest:
  return DBRequest(op="db:content:wiki:get:1", payload=params.model_dump())


def get_wiki_by_slug_request(params: GetWikiBySlugParams) -> DBRequest:
  return DBRequest(op="db:content:wiki:get_by_slug:1", payload=params.model_dump())


def get_wiki_by_route_context_request(params: GetWikiByRouteContextParams) -> DBRequest:
  return DBRequest(op="db:content:wiki:get_by_route_context:1", payload=params.model_dump())


def list_children_request(params: ListChildrenParams) -> DBRequest:
  return DBRequest(op="db:content:wiki:list_children:1", payload=params.model_dump())


def create_wiki_request(params: CreateWikiParams) -> DBRequest:
  return DBRequest(op="db:content:wiki:create:1", payload=params.model_dump())


def update_wiki_request(params: UpdateWikiParams) -> DBRequest:
  return DBRequest(op="db:content:wiki:update:1", payload=params.model_dump())


def delete_wiki_request(params: DeleteWikiParams) -> DBRequest:
  return DBRequest(op="db:content:wiki:delete:1", payload=params.model_dump())


def create_version_request(params: CreateWikiVersionParams) -> DBRequest:
  return DBRequest(op="db:content:wiki:create_version:1", payload=params.model_dump())


def list_versions_request(params: ListWikiVersionsParams) -> DBRequest:
  return DBRequest(op="db:content:wiki:list_versions:1", payload=params.model_dump())


def get_version_request(params: GetWikiVersionParams) -> DBRequest:
  return DBRequest(op="db:content:wiki:get_version:1", payload=params.model_dump())
