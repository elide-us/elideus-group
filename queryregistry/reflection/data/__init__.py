"""Reflection data query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import BatchParams, DumpTableParams, UpdateVersionParams

__all__ = [
  "apply_batch_request",
  "dump_table_request",
  "get_version_request",
  "rebuild_indexes_request",
  "update_version_request",
]


def get_version_request() -> DBRequest:
  return DBRequest(op="db:reflection:data:get_version:1", payload={})


def update_version_request(params: UpdateVersionParams) -> DBRequest:
  return DBRequest(op="db:reflection:data:update_version:1", payload=params.model_dump())


def dump_table_request(params: DumpTableParams) -> DBRequest:
  return DBRequest(op="db:reflection:data:dump_table:1", payload=params.model_dump())


def rebuild_indexes_request() -> DBRequest:
  return DBRequest(op="db:reflection:data:rebuild_indexes:1", payload={})


def apply_batch_request(params: BatchParams) -> DBRequest:
  return DBRequest(op="db:reflection:data:apply_batch:1", payload=params.model_dump())
