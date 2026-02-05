"""Database CLI module exposing management helpers."""

import ast
from pathlib import Path
from fastapi import FastAPI
import logging
from . import BaseModule
from .env_module import EnvModule
from .database_cli import mssql_cli


class DatabaseCliModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self._dsn: str | None = None
    self._queryregistry_root = Path(__file__).resolve().parents[2] / "queryregistry"

  async def startup(self):
    env: EnvModule = self.app.state.env
    await env.on_ready()
    self._dsn = env.get("AZURE_SQL_CONNECTION_STRING")
    if not self._dsn:
      logging.warning(
        "[DatabaseCli] Missing AZURE_SQL_CONNECTION_STRING; metadata-only APIs remain available"
      )
    logging.info("[DatabaseCli] module ready")
    self.mark_ready()

  async def shutdown(self):
    self._dsn = None

  async def connect(self, dbname: str | None = None):
    await self.on_ready()
    if not self._dsn:
      logging.error("[DatabaseCli] connect requested without AZURE_SQL_CONNECTION_STRING")
      raise RuntimeError("AZURE_SQL_CONNECTION_STRING not configured")
    return await mssql_cli.connect(dsn=self._dsn, dbname=dbname)

  async def reconnect(self, conn, dbname: str):
    await self.on_ready()
    if not self._dsn:
      logging.error("[DatabaseCli] reconnect requested without AZURE_SQL_CONNECTION_STRING")
      raise RuntimeError("AZURE_SQL_CONNECTION_STRING not configured")
    return await mssql_cli.reconnect(conn, dsn=self._dsn, dbname=dbname)

  async def list_tables(self, conn):
    await self.on_ready()
    return await mssql_cli.list_tables(conn)

  async def get_database_rpc_namespace(self) -> dict[str, object]:
    operations = self._discover_queryregistry_operations()
    return {
      "namespace": "db",
      "operationCount": len(operations),
      "operations": operations,
    }

  async def list_queryregistry_models(self) -> list[dict[str, str]]:
    return self._discover_queryregistry_models()

  def _discover_queryregistry_operations(self) -> list[dict[str, str]]:
    operations: list[dict[str, str]] = []
    try:
      for handler_path in sorted(self._queryregistry_root.rglob("handler.py")):
        for operation in self._parse_handler_dispatchers(handler_path):
          operations.append(operation)
    except Exception:
      logging.exception("[DatabaseCli] Failed to discover queryregistry operations")
      raise
    return operations

  def _parse_handler_dispatchers(self, handler_path: Path) -> list[dict[str, str]]:
    with handler_path.open("r", encoding="utf-8") as source_file:
      tree = ast.parse(source_file.read(), filename=str(handler_path))

    rel_dir = handler_path.parent.relative_to(self._queryregistry_root)
    parts = [] if str(rel_dir) == "." else list(rel_dir.parts)

    operations: list[dict[str, str]] = []
    for node in tree.body:
      targets: list[str] = []
      value = None
      if isinstance(node, ast.Assign):
        targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
        value = node.value
      elif isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name):
          targets = [node.target.id]
        value = node.value
      if "DISPATCHERS" not in targets or not isinstance(value, ast.Dict):
        continue

      for key, dispatcher in zip(value.keys, value.values):
        if not isinstance(key, ast.Tuple) or len(key.elts) != 2:
          continue
        op, version = key.elts
        if not isinstance(op, ast.Constant) or not isinstance(version, ast.Constant):
          continue
        if isinstance(dispatcher, ast.Name):
          func_name = dispatcher.id
        elif isinstance(dispatcher, ast.Attribute):
          func_name = dispatcher.attr
        else:
          continue

        operations.append(
          {
            "op": f"db:{':'.join(parts + [str(op.value), str(version.value)])}",
            "function": func_name,
            "handler": str(handler_path.relative_to(self._queryregistry_root.parent)).replace("\\", "/"),
          }
        )
    return operations

  def _discover_queryregistry_models(self) -> list[dict[str, str]]:
    models: list[dict[str, str]] = []
    try:
      for models_path in sorted(self._queryregistry_root.rglob("models.py")):
        models.extend(self._parse_models_file(models_path))
    except Exception:
      logging.exception("[DatabaseCli] Failed to discover queryregistry models")
      raise
    return models

  def _parse_models_file(self, models_path: Path) -> list[dict[str, str]]:
    with models_path.open("r", encoding="utf-8") as source_file:
      tree = ast.parse(source_file.read(), filename=str(models_path))

    module_name = ".".join(models_path.relative_to(self._queryregistry_root.parent).with_suffix("").parts)
    discovered: list[dict[str, str]] = []

    for node in tree.body:
      if not isinstance(node, ast.ClassDef):
        continue
      if not self._is_basemodel_subclass(node):
        continue
      discovered.append(
        {
          "name": node.name,
          "module": module_name,
          "path": str(models_path.relative_to(self._queryregistry_root.parent)).replace("\\", "/"),
        }
      )
    return discovered

  def _is_basemodel_subclass(self, node: ast.ClassDef) -> bool:
    for base in node.bases:
      if isinstance(base, ast.Name) and base.id == "BaseModel":
        return True
      if isinstance(base, ast.Attribute) and base.attr == "BaseModel":
        return True
    return False
