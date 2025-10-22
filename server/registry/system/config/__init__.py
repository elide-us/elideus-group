"""System configuration registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from server.registry.types import DBRequest
from .model import ConfigKeyParams, UpsertConfigParams

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "delete_config_request",
  "get_config_request",
  "get_configs_request",
  "register",
  "upsert_config_request",
  "ConfigKeyParams",
  "UpsertConfigParams",
]


def get_config_request(params: ConfigKeyParams) -> DBRequest:
  return DBRequest(op="db:system:config:get_config:1", params=params.model_dump())


def get_configs_request() -> DBRequest:
  return DBRequest(op="db:system:config:get_configs:1", params={})


def upsert_config_request(params: UpsertConfigParams) -> DBRequest:
  return DBRequest(
    op="db:system:config:upsert_config:1",
    params=params.model_dump(),
  )


def delete_config_request(params: ConfigKeyParams) -> DBRequest:
  return DBRequest(op="db:system:config:delete_config:1", params=params.model_dump())


def register(router: "SubdomainRouter") -> None:
  router.add_function("get_config", version=1)
  router.add_function("get_configs", version=1)
  router.add_function("upsert_config", version=1)
  router.add_function("delete_config", version=1)
