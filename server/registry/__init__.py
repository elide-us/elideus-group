"""Database registry scaffolding for DBRequest dispatch."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable, Mapping

from .models import DBRequest

logger = logging.getLogger(__name__)

@dataclass(slots=True)
class HandlerInfo:
  module: str
  attribute: str
  legacy: bool = False
  _cached: Callable[[Mapping[str, Any]], Any] | None = None

  def load(self) -> Callable[[Mapping[str, Any]], Any]:
    if self._cached is None:
      module = import_module(self.module)
      self._cached = getattr(module, self.attribute)
    return self._cached


def parse_db_op(op: str) -> tuple[str, tuple[str, ...], int]:
  parts = op.split(":")
  if len(parts) < 4 or parts[0] != "db":
    raise ValueError(f"Invalid database operation: {op}")
  *segments, version_str = parts[1:]
  try:
    version = int(version_str)
  except ValueError as exc:
    raise ValueError(f"Invalid DB operation version: {op}") from exc
  domain, *path = segments
  return domain, tuple(path), version


def _build_handler_info(
  op: str,
  *,
  provider: str,
  log_errors: bool = True,
) -> HandlerInfo:
  domain, path, version = parse_db_op(op)
  if not path:
    raise ValueError(f"Invalid database operation path: {op}")
  *subpath, operation = path
  module = ".".join(("server", "registry", domain, *subpath, provider))
  attribute = f"{operation}_v{version}"
  info = HandlerInfo(module=module, attribute=attribute)
  try:
    info.load()
  except (ModuleNotFoundError, AttributeError) as exc:
    if log_errors:
      logger.error(
        "Registry handler resolution failed",
        extra={"db_op": op, "db_provider": provider},
        exc_info=False,
      )
    raise KeyError(
      f"No handler registered for operation '{op}' with provider '{provider}'"
    ) from exc
  return info


def get_handler(op: str, *, provider: str = "mssql") -> Callable[[Mapping[str, Any]], Any]:
  info = _build_handler_info(op, provider=provider)
  logger.info(
    "Registry handler resolved",
    extra={"db_op": op, "db_provider": provider},
  )
  return info.load()


def get_handler_info(
  op: str,
  *,
  provider: str = "mssql",
  log_resolution: bool = True,
) -> HandlerInfo:
  info = _build_handler_info(op, provider=provider)
  if log_resolution:
    logger.info(
      "Registry handler resolved",
      extra={"db_op": op, "db_provider": provider},
    )
  return info


def try_get_handler_info(
  op: str,
  *,
  provider: str = "mssql",
) -> HandlerInfo | None:
  try:
    return _build_handler_info(op, provider=provider, log_errors=False)
  except KeyError:
    return None
