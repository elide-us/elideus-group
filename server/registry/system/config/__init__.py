"""System configuration registry bindings."""

from __future__ import annotations

from server.registry.types import DBRequest
from .model import ConfigKeyParams, UpsertConfigParams

__all__ = [
  "delete_config_request",
  "get_config_request",
  "get_configs_request",
  "upsert_config_request",
  "ConfigKeyParams",
  "UpsertConfigParams",
]


def get_config_request(params: ConfigKeyParams) -> DBRequest:
  return DBRequest(op="db:system:config:get_config:1", payload=params.model_dump())


def get_configs_request() -> DBRequest:
  return DBRequest(op="db:system:config:get_configs:1", payload={})


def upsert_config_request(params: UpsertConfigParams) -> DBRequest:
  return DBRequest(
    op="db:system:config:upsert_config:1",
    payload=params.model_dump(),
  )


def delete_config_request(params: ConfigKeyParams) -> DBRequest:
  return DBRequest(op="db:system:config:delete_config:1", payload=params.model_dump())
