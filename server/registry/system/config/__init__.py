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
  router.add_function("get_config", version=1)
  router.add_function("get_configs", version=1)
  router.add_function("upsert_config", version=1)
  router.add_function("delete_config", version=1)
