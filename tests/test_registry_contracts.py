"""Sanity checks for registry metadata and operation naming conventions."""

from __future__ import annotations

import importlib
import inspect
import re
from pathlib import Path

from server.registry import get_handler_info, parse_db_op, try_get_handler_info


def _iter_provider_operations():
  base = Path("server/registry")
  for module_path in base.rglob("mssql.py"):
    if "providers" in module_path.parts:
      continue
    module_name = ".".join(module_path.with_suffix("").parts)
    module = importlib.import_module(module_name)
    parts = module_name.split(".")
    registry_index = parts.index("registry")
    domain = parts[registry_index + 1]
    subpath = tuple(parts[registry_index + 2 : -1])
    for name, func in inspect.getmembers(module, inspect.iscoroutinefunction):
      match = re.fullmatch(r"(?P<operation>.+)_v(?P<version>\d+)", name)
      if not match:
        continue
      operation = match.group("operation")
      version = int(match.group("version"))
      op = ":".join(("db", domain, *subpath, operation, str(version)))
      yield op, domain, subpath, version, func


def test_provider_modules_align_with_dynamic_resolution():
  for op, domain, subpath, version, func in _iter_provider_operations():
    info = try_get_handler_info(op, provider="mssql")
    if info is None:
      continue
    handler = info.load()
    assert handler is func, f"{op} should resolve to {func.__module__}.{func.__name__}"
    resolved_domain, path, resolved_version = parse_db_op(op)
    assert resolved_domain == domain
    assert resolved_version == version
    assert tuple(path[:-1]) == subpath
    assert path[-1] == op.split(":")[-2]
    info_direct = get_handler_info(op, provider="mssql", log_resolution=False)
    assert info_direct.load() is handler
