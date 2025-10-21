"""Account cache registry bindings.

Request helpers in this package now accept validated Pydantic models defined in
``model.py``.  Using those models keeps database contracts aligned across
services and providers while providing eager validation for shared payloads.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, TYPE_CHECKING

from .model import (
  CacheItemKey,
  ContentCacheItem,
  DeleteCacheFolderParams,
  ListCacheParams,
  ReplaceUserCacheParams,
  SetPublicParams,
  SetReportedParams,
  UpsertCacheItemParams,
  normalize_content_cache_item,
)

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "register",
  "delete_cache_folder_request",
  "delete_cache_item_request",
  "set_public_request",
  "set_reported_request",
  "list_cache_request",
  "list_public_request",
  "list_reported_request",
  "replace_user_cache_request",
  "upsert_cache_item_request",
  "count_rows_request",
  "ContentCacheItem",
  "CacheItemKey",
  "DeleteCacheFolderParams",
  "ListCacheParams",
  "ReplaceUserCacheParams",
  "SetPublicParams",
  "SetReportedParams",
  "UpsertCacheItemParams",
  "normalize_content_cache_item",
]


def _normalize_cache_item_payload(
  item: Mapping[str, Any] | ContentCacheItem,
  *,
  default_user_guid: str | None = None,
) -> Dict[str, Any]:
  payload = normalize_content_cache_item(
    item,
    default_user_guid=default_user_guid,
  )
  if default_user_guid and not payload.get("user_guid"):
    payload["user_guid"] = default_user_guid
  return payload


def list_cache_request(params: ListCacheParams) -> DBRequest:
  from server.registry.types import DBRequest
  return DBRequest(
    op="db:account:cache:list:1",
    params=params.model_dump(),
  )


def list_public_request():
  from server.registry.types import DBRequest
  return DBRequest(op="db:account:cache:list_public:1", params={})


def list_reported_request():
  from server.registry.types import DBRequest
  return DBRequest(op="db:account:cache:list_reported:1", params={})


def replace_user_cache_request(params: ReplaceUserCacheParams) -> DBRequest:
  from server.registry.types import DBRequest
  normalized_items = [item.model_dump() for item in params.items]
  payload = params.model_dump()
  payload["items"] = normalized_items
  return DBRequest(op="db:account:cache:replace_user:1", params=payload)


def upsert_cache_item_request(item: UpsertCacheItemParams | Dict[str, Any]):
  from server.registry.types import DBRequest
  if isinstance(item, UpsertCacheItemParams):
    normalized = item.model_dump()
  else:
    normalized = _normalize_cache_item_payload(item)
  return DBRequest(op="db:account:cache:upsert:1", params=normalized)


def delete_cache_item_request(params: CacheItemKey) -> DBRequest:
  from server.registry.types import DBRequest
  return DBRequest(op="db:account:cache:delete:1", params=params.model_dump())


def delete_cache_folder_request(params: DeleteCacheFolderParams) -> DBRequest:
  from server.registry.types import DBRequest
  return DBRequest(op="db:account:cache:delete_folder:1", params=params.model_dump())


def set_public_request(params: SetPublicParams) -> DBRequest:
  from server.registry.types import DBRequest
  payload = params.model_dump(exclude_none=True)
  payload["public"] = 1 if params.public else 0
  return DBRequest(op="db:account:cache:set_public:1", params=payload)


def set_reported_request(params: SetReportedParams) -> DBRequest:
  from server.registry.types import DBRequest
  payload = params.model_dump()
  payload["reported"] = 1 if params.reported else 0
  return DBRequest(op="db:account:cache:set_reported:1", params=payload)


def count_rows_request():
  from server.registry.types import DBRequest
  return DBRequest(op="db:account:cache:count_rows:1", params={})


def register(router: "SubdomainRouter") -> None:
  router.add_function("list", version=1)
  router.add_function("list_public", version=1)
  router.add_function("list_reported", version=1)
  router.add_function("replace_user", version=1)
  router.add_function("upsert", version=1)
  router.add_function("delete", version=1)
  router.add_function("delete_folder", version=1)
  router.add_function("set_public", version=1)
  router.add_function("set_reported", version=1)
  router.add_function("count_rows", version=1)
