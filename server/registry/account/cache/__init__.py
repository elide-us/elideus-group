"""Account cache registry bindings.

Request helpers in this package now accept validated Pydantic models defined in
``model.py``.  Using those models keeps database contracts aligned across
services and providers while providing eager validation for shared payloads.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping

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
    payload=params.model_dump(),
  )


def list_public_request():
  from server.registry.types import DBRequest
  return DBRequest(op="db:account:cache:list_public:1", payload={})


def list_reported_request():
  from server.registry.types import DBRequest
  return DBRequest(op="db:account:cache:list_reported:1", payload={})


def replace_user_cache_request(params: ReplaceUserCacheParams) -> DBRequest:
  from server.registry.types import DBRequest
  normalized_items = [item.model_dump() for item in params.items]
  payload = params.model_dump()
  payload["items"] = normalized_items
  return DBRequest(op="db:account:cache:replace_user:1", payload=payload)


def upsert_cache_item_request(item: UpsertCacheItemParams | Dict[str, Any]):
  from server.registry.types import DBRequest
  if isinstance(item, UpsertCacheItemParams):
    normalized = item.model_dump()
  else:
    normalized = _normalize_cache_item_payload(item)
  return DBRequest(op="db:account:cache:upsert:1", payload=normalized)


def delete_cache_item_request(params: CacheItemKey) -> DBRequest:
  from server.registry.types import DBRequest
  return DBRequest(op="db:account:cache:delete:1", payload=params.model_dump())


def delete_cache_folder_request(params: DeleteCacheFolderParams) -> DBRequest:
  from server.registry.types import DBRequest
  return DBRequest(op="db:account:cache:delete_folder:1", payload=params.model_dump())


def set_public_request(params: SetPublicParams) -> DBRequest:
  from server.registry.types import DBRequest
  payload = params.model_dump(exclude_none=True)
  payload["public"] = 1 if params.public else 0
  return DBRequest(op="db:account:cache:set_public:1", payload=payload)


def set_reported_request(params: SetReportedParams) -> DBRequest:
  from server.registry.types import DBRequest
  payload = params.model_dump()
  payload["reported"] = 1 if params.reported else 0
  return DBRequest(op="db:account:cache:set_reported:1", payload=payload)


def count_rows_request():
  from server.registry.types import DBRequest
  return DBRequest(op="db:account:cache:count_rows:1", payload={})
