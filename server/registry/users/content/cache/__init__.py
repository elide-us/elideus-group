"""Content cache registry bindings."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, TYPE_CHECKING

from .model import ContentCacheItem, normalize_content_cache_item

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
  "normalize_content_cache_item",
]


def _normalize_cache_item_payload(
  item: Mapping[str, Any] | ContentCacheItem,
  *,
  default_user_guid: str | None = None,
) -> Dict[str, Any]:
  if isinstance(item, ContentCacheItem):
    payload = item.to_payload()
  else:
    payload = normalize_content_cache_item(item, default_user_guid=default_user_guid)
  if default_user_guid and not payload.get("user_guid"):
    payload["user_guid"] = default_user_guid
  return payload


def list_cache_request(user_guid: str):
  from server.registry.types import DBRequest
  return DBRequest(op="db:users:content:content_cache:list:1", params={"user_guid": user_guid})


def list_public_request():
  from server.registry.types import DBRequest
  return DBRequest(op="db:users:content:content_cache:list_public:1", params={})


def list_reported_request():
  from server.registry.types import DBRequest
  return DBRequest(op="db:users:content:content_cache:list_reported:1", params={})


def replace_user_cache_request(user_guid: str, items: Iterable[Dict[str, Any]]):
  from server.registry.types import DBRequest
  normalized = [
    _normalize_cache_item_payload(item, default_user_guid=user_guid)
    for item in items
  ]
  return DBRequest(op="db:users:content:content_cache:replace_user:1", params={
    "user_guid": user_guid,
    "items": normalized,
  })


def upsert_cache_item_request(item: Dict[str, Any]):
  from server.registry.types import DBRequest
  normalized = _normalize_cache_item_payload(item)
  return DBRequest(op="db:users:content:content_cache:upsert:1", params=normalized)


def delete_cache_item_request(user_guid: str, path: str, filename: str):
  from server.registry.types import DBRequest
  return DBRequest(op="db:users:content:content_cache:delete:1", params={
    "user_guid": user_guid,
    "path": path,
    "filename": filename,
  })


def delete_cache_folder_request(user_guid: str, path: str):
  from server.registry.types import DBRequest
  return DBRequest(op="db:users:content:content_cache:delete_folder:1", params={
    "user_guid": user_guid,
    "path": path,
  })


def set_public_request(
  user_guid: str,
  *,
  public: bool,
  name: str | None = None,
  path: str | None = None,
  filename: str | None = None,
):
  from server.registry.types import DBRequest
  params = {
    "user_guid": user_guid,
    "public": bool(public),
  }
  if name is not None:
    params["name"] = name
  if path is not None:
    params["path"] = path
  if filename is not None:
    params["filename"] = filename
  return DBRequest(op="db:users:content:content_cache:set_public:1", params=params)


def set_reported_request(
  user_guid: str,
  *,
  path: str,
  filename: str,
  reported: bool = True,
):
  from server.registry.types import DBRequest
  return DBRequest(op="db:users:content:content_cache:set_reported:1", params={
    "user_guid": user_guid,
    "path": path,
    "filename": filename,
    "reported": bool(reported),
  })


def count_rows_request():
  from server.registry.types import DBRequest
  return DBRequest(op="db:users:content:content_cache:count_rows:1", params={})


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
