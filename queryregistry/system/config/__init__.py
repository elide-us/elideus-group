"""System config query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import ConfigKeyParams, UpsertConfigParams

__all__ = [
  "delete_config_request",
  "get_config_request",
  "get_configs_request",
  "upsert_config_request",
]


def get_config_request(params: ConfigKeyParams) -> DBRequest:
  return DBRequest(op="db:system:config:get:1", payload=params.model_dump())


def get_configs_request() -> DBRequest:
  return DBRequest(op="db:system:config:list:1", payload={})


def upsert_config_request(params: UpsertConfigParams) -> DBRequest:
  return DBRequest(op="db:system:config:upsert:1", payload=params.model_dump())


def delete_config_request(params: ConfigKeyParams) -> DBRequest:
  return DBRequest(op="db:system:config:delete:1", payload=params.model_dump())
