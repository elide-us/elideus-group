"""MSSQL provider callable bindings."""

from __future__ import annotations

import importlib
import inspect
from collections.abc import Iterable
from typing import Any

import logging

from server.registry import ProviderBinding, RegistryRouter
from server.registry.types import DBRequest, DBResponse
from server.helpers.context import get_request_id

from . import ProviderCallable, ProviderDescriptor, ProviderQueryMap, RawProvider

__all__ = [
  "PROVIDER_QUERIES",
  "run_exec",
  "run_json_many",
  "run_json_one",
]


def _get_provider():
  return importlib.import_module("server.modules.providers.database.mssql_provider")


_logger = logging.getLogger(__name__)


async def _run_operation(kind: str, sql: str, params: Iterable[Any] = (), *, meta: dict[str, Any] | None = None) -> DBResponse:
  provider = _get_provider()
  request_id = get_request_id()
  payload_meta = dict(meta or {})
  if request_id and payload_meta.get('request_id') != request_id:
    payload_meta['request_id'] = request_id
  if request_id:
    _logger.debug('[MSSQL %s] Executing query %s', request_id, sql.split()[0])
  result = await provider.run_operation(kind, sql, tuple(params))
  if request_id:
    _logger.debug('[MSSQL %s] Query completed %s', request_id, sql.split()[0])
  return DBResponse.from_result(result, meta=payload_meta or None)


async def run_json_one(sql: str, params: Iterable[Any] = (), *, meta: dict[str, Any] | None = None) -> DBResponse:
  return await _run_operation("json_one", sql, params, meta=meta)


async def run_json_many(sql: str, params: Iterable[Any] = (), *, meta: dict[str, Any] | None = None) -> DBResponse:
  return await _run_operation("json_many", sql, params, meta=meta)


async def run_exec(sql: str, params: Iterable[Any] = (), *, meta: dict[str, Any] | None = None) -> DBResponse:
  return await _run_operation("exec", sql, params, meta=meta)


async def _coerce_response(spec: Any) -> DBResponse:
  if inspect.isawaitable(spec):
    spec = await spec
  if not isinstance(spec, DBResponse):
    raise TypeError(f"Expected DBResponse from provider callable, received {type(spec)!r}")
  return spec


def _wrap(fn: RawProvider) -> ProviderCallable:
  async def _executor(request: DBRequest) -> DBResponse:
    spec = fn(request.params)
    return await _coerce_response(spec)
  return _executor


def _resolve_descriptor(descriptor: ProviderDescriptor) -> RawProvider:
  if callable(descriptor):
    return descriptor
  module_path, attr_name = descriptor

  def _invoke(params: dict[str, Any]) -> Any:
    module = importlib.import_module(module_path)
    fn = getattr(module, attr_name)
    return fn(params)

  return _invoke


def _wrap_descriptor(descriptor: ProviderDescriptor) -> ProviderCallable:
  raw = _resolve_descriptor(descriptor)
  return _wrap(raw)


def _collect_bindings(
  bindings: Iterable[ProviderBinding] | None,
) -> list[ProviderBinding]:
  if bindings is not None:
    return list(bindings)
  router = RegistryRouter()
  router.register_domains()
  return list(router.provider_bindings.values())


def build_provider_queries(
  bindings: Iterable[ProviderBinding] | None = None,
) -> dict[str, dict[int, ProviderCallable]]:
  collected = _collect_bindings(bindings)
  queries: dict[str, dict[int, ProviderCallable]] = {}
  for binding in collected:
    descriptor = binding.descriptor
    if descriptor is None:
      raise ValueError(
        f"Route '{binding.canonical}' does not declare a provider binding for MSSQL",
      )
    versions = queries.setdefault(binding.provider_map, {})
    if binding.version in versions:
      raise ValueError(
        f"Duplicate MSSQL provider binding for '{binding.provider_map}' version {binding.version}",
      )
    versions[binding.version] = _wrap_descriptor(descriptor)
  return {key: value.copy() for key, value in queries.items()}


_PROVIDER_QUERIES: ProviderQueryMap | None = None
PROVIDER_QUERIES: ProviderQueryMap = {}


def get_provider_queries(
  bindings: Iterable[ProviderBinding] | None = None,
) -> ProviderQueryMap:
  global _PROVIDER_QUERIES
  if bindings is not None:
    return build_provider_queries(bindings)
  if _PROVIDER_QUERIES is None:
    importlib.import_module("server.registry.users")
    importlib.import_module("server.registry.finance")
    importlib.import_module("server.registry.system")
    base = build_provider_queries()
    if not any(key.startswith("users.") for key in base):
      base = build_provider_queries()
    if PROVIDER_QUERIES:
      # Allow test overrides to win when populating the cache for the first time.
      base.update(PROVIDER_QUERIES)
    _PROVIDER_QUERIES = base
    PROVIDER_QUERIES.clear()
    PROVIDER_QUERIES.update(_PROVIDER_QUERIES)
  return PROVIDER_QUERIES


if not PROVIDER_QUERIES:
  try:
    get_provider_queries()
  except Exception:
    _PROVIDER_QUERIES = None
