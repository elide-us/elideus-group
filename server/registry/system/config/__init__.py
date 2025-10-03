"""System configuration registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "delete_config_request",
  "get_config_request",
  "get_configs_request",
  "register",
  "upsert_config_request",
]

_DEF_PROVIDER = "system.config"
_PROVIDER_MODULE = "server.registry.system.config.mssql"
_PROVIDER_ATTRS: dict[str, str] = {
  "get_config": "get_config_v1",
  "get_configs": "get_configs_v1",
  "upsert_config": "upsert_config_v1",
  "delete_config": "delete_config_v1",
}


def get_config_request(key: str) -> DBRequest:
  return DBRequest(op="db:system:config:get_config:1", params={"key": key})


def get_configs_request() -> DBRequest:
  return DBRequest(op="db:system:config:get_configs:1", params={})


def upsert_config_request(key: str, value: str) -> DBRequest:
  return DBRequest(op="db:system:config:upsert_config:1", params={
    "key": key,
    "value": value,
  })


def delete_config_request(key: str) -> DBRequest:
  return DBRequest(op="db:system:config:delete_config:1", params={"key": key})


def register(router: "SubdomainRouter") -> None:
  for name, attr in _PROVIDER_ATTRS.items():
    router.add_function(
      name,
      version=1,
      provider_map=f"{_DEF_PROVIDER}.{name}",
      provider=(_PROVIDER_MODULE, attr),
    )
