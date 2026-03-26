"""Content indexing query registry request builders."""

from __future__ import annotations

from typing import Any, Mapping

from queryregistry.models import DBRequest

from .models import (
  CacheItemKey,
  ContentCacheItem,
  DeleteCacheFolderParams,
  GetPublishedFilesParams,
  ListCacheParams,
  ReplaceUserCacheParams,
  SetGalleryParams,
  SetPublicParams,
  SetReportedParams,
  UpsertCacheItemParams,
  normalize_content_cache_item,
)

__all__ = [
  "count_rows_request",
  "delete_cache_folder_request",
  "delete_cache_item_request",
  "get_published_files_request",
  "list_cache_request",
  "list_public_request",
  "list_reported_request",
  "replace_user_cache_request",
  "set_gallery_request",
  "set_public_request",
  "set_reported_request",
  "upsert_cache_item_request",
]


def _normalize_cache_item_payload(
  item: Mapping[str, Any] | ContentCacheItem,
  *,
  default_user_guid: str | None = None,
) -> dict[str, Any]:
  payload = normalize_content_cache_item(item, default_user_guid=default_user_guid)
  if default_user_guid and not payload.get("user_guid"):
    payload["user_guid"] = default_user_guid
  return payload


def list_cache_request(params: ListCacheParams) -> DBRequest:
  return DBRequest(op="db:content:indexing:list:1", payload=params.model_dump())


def list_public_request() -> DBRequest:
  return DBRequest(op="db:content:indexing:list_public:1", payload={})


def list_reported_request() -> DBRequest:
  return DBRequest(op="db:content:indexing:list_reported:1", payload={})


def replace_user_cache_request(params: ReplaceUserCacheParams) -> DBRequest:
  payload = params.model_dump()
  payload["items"] = [item.model_dump() for item in params.items]
  return DBRequest(op="db:content:indexing:replace_user:1", payload=payload)


def upsert_cache_item_request(item: UpsertCacheItemParams | dict[str, Any]) -> DBRequest:
  if isinstance(item, UpsertCacheItemParams):
    normalized = item.model_dump()
  else:
    normalized = _normalize_cache_item_payload(item)
  return DBRequest(op="db:content:indexing:upsert:1", payload=normalized)


def delete_cache_item_request(params: CacheItemKey) -> DBRequest:
  return DBRequest(op="db:content:indexing:delete:1", payload=params.model_dump())


def delete_cache_folder_request(params: DeleteCacheFolderParams) -> DBRequest:
  return DBRequest(op="db:content:indexing:delete_folder:1", payload=params.model_dump())


def set_public_request(params: SetPublicParams) -> DBRequest:
  payload = params.model_dump(exclude_none=True)
  payload["public"] = 1 if params.public else 0
  return DBRequest(op="db:content:indexing:set_public:1", payload=payload)


def set_reported_request(params: SetReportedParams) -> DBRequest:
  payload = params.model_dump()
  payload["reported"] = 1 if params.reported else 0
  return DBRequest(op="db:content:indexing:set_reported:1", payload=payload)


def count_rows_request() -> DBRequest:
  return DBRequest(op="db:content:indexing:count_rows:1", payload={})


def set_gallery_request(params: SetGalleryParams) -> DBRequest:
  payload = params.model_dump(exclude_none=True)
  payload["gallery"] = 1 if params.gallery else 0
  return DBRequest(op="db:content:indexing:set_gallery:1", payload=payload)


def get_published_files_request(params: GetPublishedFilesParams) -> DBRequest:
  return DBRequest(op="db:content:indexing:get_published_files:1", payload=params.model_dump())
