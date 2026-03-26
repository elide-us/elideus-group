"""Content pages query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  CreatePageParams,
  CreateVersionParams,
  DeletePageParams,
  GetPageBySlugParams,
  GetPageParams,
  GetVersionParams,
  ListPagesParams,
  ListVersionsParams,
  UpdatePageParams,
)

__all__ = [
  "create_page_request",
  "create_version_request",
  "delete_page_request",
  "get_page_by_slug_request",
  "get_page_request",
  "get_version_request",
  "list_pages_request",
  "list_versions_request",
  "update_page_request",
]


def list_pages_request(params: ListPagesParams) -> DBRequest:
  return DBRequest(op="db:content:pages:list:1", payload=params.model_dump())


def get_page_request(params: GetPageParams) -> DBRequest:
  return DBRequest(op="db:content:pages:get:1", payload=params.model_dump())


def get_page_by_slug_request(params: GetPageBySlugParams) -> DBRequest:
  return DBRequest(op="db:content:pages:get_by_slug:1", payload=params.model_dump())


def create_page_request(params: CreatePageParams) -> DBRequest:
  return DBRequest(op="db:content:pages:create:1", payload=params.model_dump())


def update_page_request(params: UpdatePageParams) -> DBRequest:
  return DBRequest(op="db:content:pages:update:1", payload=params.model_dump())


def delete_page_request(params: DeletePageParams) -> DBRequest:
  return DBRequest(op="db:content:pages:delete:1", payload=params.model_dump())


def create_version_request(params: CreateVersionParams) -> DBRequest:
  return DBRequest(op="db:content:pages:create_version:1", payload=params.model_dump())


def list_versions_request(params: ListVersionsParams) -> DBRequest:
  return DBRequest(op="db:content:pages:list_versions:1", payload=params.model_dump())


def get_version_request(params: GetVersionParams) -> DBRequest:
  return DBRequest(op="db:content:pages:get_version:1", payload=params.model_dump())
