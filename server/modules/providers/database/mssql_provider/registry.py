"""Compatibility helpers for MSSQL registry tests."""

from __future__ import annotations

import importlib
from collections.abc import Mapping
from typing import Any

from server.modules.providers import DBResult
from server.registry.providers.mssql import _PROVIDER_SPECS
from server.registry.security.identities import mssql as identities_mssql

transaction = identities_mssql.transaction
get_auth_provider_recid = identities_mssql.get_auth_provider_recid
fetch_json = identities_mssql.fetch_json

__all__ = [
  "fetch_json",
  "get_auth_provider_recid",
  "get_handler",
  "transaction",
  "_users_unlink_provider",
]


def _resolve_provider_entry(urn: str) -> tuple[str, str]:
  parts = urn.split(":")
  if len(parts) != 5 or parts[0] != "db":
    raise KeyError(f"Unsupported operation key: {urn}")
  _, domain, subdomain, name, version = parts
  provider_map = f"{domain}.{subdomain}.{name}"
  entry = _PROVIDER_SPECS.get(provider_map)
  if entry is None:
    raise KeyError(f"No provider specification for '{urn}'")
  try:
    version_int = int(version)
  except ValueError as exc:
    raise KeyError(f"Invalid operation version for '{urn}'") from exc
  if version_int != 1:
    raise KeyError(f"No handler for '{urn}'")
  return entry


def get_handler(urn: str):
  module_path, attr_name = _resolve_provider_entry(urn)
  module = importlib.import_module(module_path)
  handler = getattr(module, attr_name)
  if handler is None:
    raise KeyError(f"No handler for '{urn}'")
  return handler


async def _users_unlink_provider(args: dict[str, Any]) -> dict[str, Any]:
  current_transaction = transaction
  original_transaction = identities_mssql.transaction
  try:
    identities_mssql.transaction = current_transaction
    result = await identities_mssql.unlink_provider_v1(args)
  finally:
    identities_mssql.transaction = original_transaction
  if isinstance(result, DBResult):
    return result.model_dump()
  if hasattr(result, "model_dump"):
    return result.model_dump()
  if isinstance(result, Mapping):
    return dict(result)
  return {"rows": getattr(result, "rows", []), "rowcount": getattr(result, "rowcount", 0)}
