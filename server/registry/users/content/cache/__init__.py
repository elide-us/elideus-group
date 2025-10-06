"""Content cache registry bindings."""

from __future__ import annotations

from typing import Any, Dict, Iterable, TYPE_CHECKING

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "register",
  "delete_cache_folder_request",
  "delete_cache_item_request",
  "set_public_request",
  "set_reported_request",
  "list_cache_request",
  "replace_user_cache_request",
  "upsert_cache_item_request",
  "count_rows_request",
]


def _normalize_cache_item_payload(item: Dict[str, Any]) -> Dict[str, Any]:
  normalized = dict(item)
  name = normalized.get("filename") or normalized.get("name")
  if name is not None:
    normalized["filename"] = name
  if "path" not in normalized or normalized["path"] is None:
    normalized["path"] = ""
  for flag in ("public", "reported"):
    if flag in normalized and normalized[flag] is not None:
      normalized[flag] = 1 if normalized[flag] else 0
  return normalized


def list_cache_request(user_guid: str):
  from server.registry.types import DBRequest
  return DBRequest(op="db:users:content.cache:list:1", params={"user_guid": user_guid})


def replace_user_cache_request(user_guid: str, items: Iterable[Dict[str, Any]]):
  from server.registry.types import DBRequest
  normalized = [_normalize_cache_item_payload(item) for item in items]
  return DBRequest(op="db:users:content.cache:replace_user:1", params={
    "user_guid": user_guid,
    "items": normalized,
  })


def upsert_cache_item_request(item: Dict[str, Any]):
  from server.registry.types import DBRequest
  normalized = _normalize_cache_item_payload(item)
  return DBRequest(op="db:users:content.cache:upsert:1", params=normalized)


def delete_cache_item_request(user_guid: str, path: str, filename: str):
  from server.registry.types import DBRequest
  return DBRequest(op="db:users:content.cache:delete:1", params={
    "user_guid": user_guid,
    "path": path,
    "filename": filename,
  })


def delete_cache_folder_request(user_guid: str, path: str):
  from server.registry.types import DBRequest
  return DBRequest(op="db:users:content.cache:delete_folder:1", params={
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
  return DBRequest(op="db:users:content.cache:set_public:1", params=params)


def set_reported_request(
  user_guid: str,
  *,
  path: str,
  filename: str,
  reported: bool = True,
):
  from server.registry.types import DBRequest
  return DBRequest(op="db:users:content.cache:set_reported:1", params={
    "user_guid": user_guid,
    "path": path,
    "filename": filename,
    "reported": bool(reported),
  })


def count_rows_request():
  from server.registry.types import DBRequest
  return DBRequest(op="db:users:content.cache:count_rows:1", params={})


def register(router: "SubdomainRouter") -> None:
  router.add_function("list", version=1)
  router.add_function("replace_user", version=1)
  router.add_function("upsert", version=1)
  router.add_function("delete", version=1)
  router.add_function("delete_folder", version=1)
  router.add_function("set_public", version=1)
  router.add_function("set_reported", version=1)
  router.add_function("count_rows", version=1)
