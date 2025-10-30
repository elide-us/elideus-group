"""System configuration registry bindings."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from server.registry.types import DBRequest
from .model import ConfigKeyParams, UpsertConfigParams

if TYPE_CHECKING:
  from server.registry import RegistryRouter

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


def register(
  router: "RegistryRouter",
  *,
  domain: str,
  path: tuple[str, ...],
) -> None:
  register_op = partial(router.register_function, domain=domain, path=path)
  register_op(name="get_config", version=1)
  register_op(name="get_configs", version=1)
  register_op(name="upsert_config", version=1)
  register_op(name="delete_config", version=1)
