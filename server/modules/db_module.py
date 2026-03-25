"""Database module loader."""

from importlib import import_module
from typing import Any, Dict
import inspect
from fastapi import FastAPI
import logging

from queryregistry.handler import dispatch_query_request
from queryregistry.system.config.models import ConfigKeyParams
from . import BaseModule
from .env_module import EnvModule
from .providers import DbProviderBase
from queryregistry.models import DBRequest, DBResponse
from queryregistry.system.config import get_config_request
from queryregistry.helpers import parse_query_operation
from server.helpers.logging import update_logging_level


_QUIET_OPS = frozenset({
  "db:system:batch_jobs:list_jobs",
  "db:system:async_tasks:list_tasks",
  "db:system:async_tasks:update_task",
  "db:system:async_tasks:create_task_event",
})


class DbModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.provider: str = "mssql"
    self.logging_level: int = 0
    self._provider: DbProviderBase | None = None

  async def init(self, provider: str | None = None, **cfg):
    """Initialize database provider.

    Provider name can be supplied directly, via a ``provider`` key in ``cfg``, or
    from the ``DATABASE_PROVIDER`` environment variable. Defaults to ``mssql``.
    """

    config = dict(cfg)
    provider_name = provider or config.pop("provider", None) or "mssql"
    self.provider = provider_name

    try:
      module = import_module(f".providers.database.{provider_name}_provider", __package__)
    except ModuleNotFoundError as e:
      raise ValueError(f"Unsupported provider: {provider_name}") from e

    provider_cls = None
    for attr in module.__dict__.values():
      if inspect.isclass(attr) and attr.__name__ != "DbProviderBase":
        bases = inspect.getmro(attr)
        if any(b.__name__ == "DbProviderBase" for b in bases) and not inspect.isabstract(attr):
          provider_cls = attr
          break
    if not provider_cls:
      raise ValueError(f"Provider '{provider_name}' missing DbProviderBase implementation")

    self._provider = provider_cls(**config)

  def _resolve_provider_config(self, provider_name: str, env: EnvModule, overrides: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Return configuration for ``provider_name`` from environment."""
    cfg: Dict[str, Any] = {}
    if provider_name == "mssql":
      dsn = env.get("AZURE_SQL_CONNECTION_STRING")
      if dsn:
        cfg["dsn"] = dsn
    if overrides:
      cfg.update(overrides)
    return cfg

  async def run(self, request: DBRequest) -> DBResponse:
    assert self._provider, "db_module not initialized"
    if not isinstance(request, DBRequest):
      raise TypeError("DbModule.run requires a DBRequest instance")
    op = request.op
    provider_name = self.provider
    registry_logger = logging.getLogger("server" + ".registry")

    try:
      parse_query_operation(op)
    except ValueError:
      raise ValueError(f"Invalid database operation: {op}")

    op_without_version = op.rsplit(":", 1)[0]
    if op_without_version in _QUIET_OPS:
      registry_logger.debug("DB completed: %s", op)
    else:
      registry_logger.info("DB completed: %s", op)

    response = await dispatch_query_request(request, provider=provider_name)

    if not isinstance(response, DBResponse):
      response = self._normalize_response(op, response)
    elif not response.op:
      response.attach_op(op)

    return response

  def _normalize_response(self, op: str, result: Any) -> DBResponse:
    if isinstance(result, DBResponse):
      if not result.op:
        result.attach_op(op)
      return result
    if isinstance(result, dict):
      rows = result.get("rows")
      rowcount = result.get("rowcount")
      payload = result.get("payload", rows)
      return DBResponse(op=op, payload=payload, rowcount=rowcount)
    if result is None:
      return DBResponse(op=op, payload=[], rowcount=0)
    raise TypeError(f"Unexpected database response type: {type(result)!r}")

  async def startup(self):
    env: EnvModule = self.app.state.env
    await env.on_ready()
    provider_name = env.get("DATABASE_PROVIDER") or "mssql"
    self.provider = provider_name
    cfg = self._resolve_provider_config(provider_name, env)
    await self.init(provider=provider_name, **cfg)
    assert self._provider
    await self._provider.startup()
    res = await self.run(get_config_request(ConfigKeyParams(key="LoggingLevel")))
    val = res.rows[0]["element_value"] if res.rows else "0"
    try:
      self.logging_level = int(val)
    except ValueError:
      self.logging_level = 0
    update_logging_level(self.logging_level)
    self.mark_ready()

  async def shutdown(self):
    if self._provider:
      await self._provider.shutdown()
      self._provider = None
