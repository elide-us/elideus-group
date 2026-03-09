"""Database CLI module exposing management helpers."""

import ast
import json
import logging
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI

from . import BaseModule
from .database_cli import mssql_cli
from .env_module import EnvModule


def _quote(name: str) -> str:
  return "[" + name.replace("]", "]]" ) + "]"


def _qualify(schema: str, name: str) -> str:
  return f"{_quote(schema)}.{_quote(name)}"


def _normalize_length(length: int | None) -> int | None:
  if length is None:
    return None
  if length in {-1, 0}:
    return -1
  return int(length)


def _format_data_type(col: dict) -> str:
  dtype = (col.get("data_type") or "").strip()
  if not dtype:
    return ""
  upper = dtype.upper()
  length = _normalize_length(col.get("max_length"))

  if "(" in dtype:
    return dtype
  if upper in {"NVARCHAR", "NCHAR"}:
    if length == -1:
      return f"{upper}(MAX)"
    if length is not None:
      return f"{upper}({length})"
  if upper in {"VARCHAR", "CHAR", "VARBINARY", "BINARY"}:
    if length == -1:
      return f"{upper}(MAX)"
    if length is not None:
      return f"{upper}({length})"
  return upper


def _format_column(col: dict) -> str:
  parts = [_quote(col["name"]), _format_data_type(col)]
  raw_data_type = (col.get("data_type") or "").lower()
  if col.get("identity") and "identity" not in raw_data_type:
    parts.append("IDENTITY(1, 1)")
  parts.append("NULL" if col.get("nullable", True) else "NOT NULL")
  if col.get("default"):
    parts.append(f"DEFAULT {col['default']}")
  return " ".join(parts)


def _build_create_sql(table: dict) -> str:
  table_name = _qualify(table["schema"], table["name"])
  column_lines = [_format_column(col) for col in table["columns"]]
  constraints: list[str] = []
  pk = table.get("primary_key")
  if pk and pk.get("columns"):
    clause = f"CONSTRAINT {_quote(pk['name'])} PRIMARY KEY ({', '.join(pk['columns'])})"
    constraints.append(clause)
  body = ",\n  ".join(column_lines + constraints)
  return f"CREATE TABLE {table_name} (\n  {body}\n);"


def _build_index_sql(table: dict, index: dict) -> str:
  table_name = _qualify(table["schema"], table["name"])
  parts = ["CREATE"]
  if index.get("is_unique"):
    parts.append("UNIQUE")
  parts.extend(["INDEX", _quote(index["name"]), "ON", table_name, f"({', '.join(index['key_columns'])})"])
  return " ".join(parts) + ";"


def _build_foreign_key_sql(table: dict, fk: dict) -> list[str]:
  table_name = _qualify(table["schema"], table["name"])
  ref_table = _qualify(fk["ref_schema"], fk["ref_table"])
  statement = (
    f"ALTER TABLE {table_name} ADD CONSTRAINT {_quote(fk['name'])} FOREIGN KEY "
    f"({', '.join(fk['columns'])}) REFERENCES {ref_table} ({', '.join(fk['ref_columns'])});"
  )
  return [statement]


async def get_schema_from_registry(conn) -> dict[str, list[dict]]:
  async with conn.cursor() as cur:
    await cur.execute(
      "SELECT recid, element_schema, element_name "
      "FROM system_schema_tables "
      "ORDER BY element_schema, element_name"
    )
    table_rows = await cur.fetchall()

  tables: dict[int, dict] = {}
  for row in table_rows:
    table_recid, schema_name, table_name = row
    tables[int(table_recid)] = {
      "recid": int(table_recid),
      "schema": schema_name,
      "name": table_name,
      "columns": [],
      "primary_key": None,
      "unique_constraints": [],
      "check_constraints": [],
      "foreign_keys": [],
      "indexes": [],
    }

  async with conn.cursor() as cur:
    await cur.execute(
      "SELECT c.tables_recid, c.element_name, c.element_nullable, c.element_default, "
      "c.element_max_length, c.element_is_primary_key, c.element_is_identity, c.element_ordinal, "
      "m.element_mssql_type "
      "FROM system_schema_columns c "
      "JOIN system_edt_mappings m ON c.edt_recid = m.recid "
      "ORDER BY c.tables_recid, c.element_ordinal"
    )
    for row in await cur.fetchall():
      (
        tables_recid,
        col_name,
        nullable,
        default_value,
        max_length,
        is_primary,
        is_identity,
        _ordinal,
        mssql_type,
      ) = row
      table = tables.get(int(tables_recid))
      if not table:
        continue
      table["columns"].append(
        {
          "name": col_name,
          "data_type": mssql_type,
          "max_length": max_length,
          "precision": None,
          "scale": None,
          "nullable": bool(nullable),
          "default": default_value,
          "identity": bool(is_identity),
          "identity_seed": 1,
          "identity_increment": 1,
          "rowguidcol": False,
          "computed": None,
          "computed_persisted": False,
          "collation": None,
          "is_primary_key": bool(is_primary),
        }
      )

  for table in tables.values():
    pk_columns = [_quote(col["name"]) for col in table["columns"] if col["is_primary_key"]]
    if pk_columns:
      table["primary_key"] = {
        "name": f"PK_{table['name']}",
        "type_desc": "CLUSTERED",
        "columns": pk_columns,
      }

  async with conn.cursor() as cur:
    await cur.execute(
      "SELECT i.tables_recid, i.element_name, i.element_columns, i.element_is_unique "
      "FROM system_schema_indexes i "
      "ORDER BY i.tables_recid, i.element_name"
    )
    for row in await cur.fetchall():
      tables_recid, idx_name, idx_columns, is_unique = row
      table = tables.get(int(tables_recid))
      if not table:
        continue
      key_columns = [_quote(col.strip()) for col in (idx_columns or "").split(",") if col.strip()]
      table["indexes"].append(
        {
          "name": idx_name,
          "is_unique": bool(is_unique),
          "type_desc": "",
          "has_filter": False,
          "filter_definition": None,
          "key_columns": key_columns,
          "included_columns": [],
        }
      )

  async with conn.cursor() as cur:
    await cur.execute(
      "SELECT fk.tables_recid, fk.element_column_name, fk.referenced_tables_recid, fk.element_referenced_column "
      "FROM system_schema_foreign_keys fk "
      "ORDER BY fk.tables_recid, fk.element_column_name"
    )
    fk_rows = await cur.fetchall()

  async with conn.cursor() as cur:
    await cur.execute(
      "SELECT element_schema, element_name, element_definition "
      "FROM system_schema_views "
      "ORDER BY element_schema, element_name"
    )
    view_rows = await cur.fetchall()

  views = [
    {
      "schema": row[0],
      "name": row[1],
      "definition": row[2],
    }
    for row in view_rows
  ]

  for row in fk_rows:
    tables_recid, source_column, ref_tables_recid, ref_column = row
    table = tables.get(int(tables_recid))
    ref_table = tables.get(int(ref_tables_recid))
    if not table or not ref_table:
      continue
    table["foreign_keys"].append(
      {
        "name": f"FK_{table['name']}_{source_column}_{ref_table['name']}",
        "columns": [_quote(source_column)],
        "ref_columns": [_quote(ref_column)],
        "ref_schema": ref_table["schema"],
        "ref_table": ref_table["name"],
      }
    )

  schema_name_to_recid: dict[tuple[str, str], int] = {
    (table["schema"], table["name"]): recid for recid, table in tables.items()
  }

  deps: dict[int, set[int]] = {}
  for recid, table in tables.items():
    fk_targets: set[int] = set()
    for fk in table["foreign_keys"]:
      target_recid = schema_name_to_recid.get((fk["ref_schema"], fk["ref_table"]))
      if target_recid is None or target_recid == recid:
        continue
      fk_targets.add(target_recid)
    deps[recid] = fk_targets

  ordered: list[int] = []
  visited: set[int] = set()

  def _visit(recid: int) -> None:
    if recid in visited:
      return
    visited.add(recid)
    for dep in deps.get(recid, set()):
      if dep in tables:
        _visit(dep)
    ordered.append(recid)

  for recid in tables:
    _visit(recid)

  return {"tables": [tables[recid] for recid in ordered], "views": views}


async def dump_schema_from_registry(conn, prefix: str = "schema") -> str:
  schema = await get_schema_from_registry(conn)
  ts = datetime.now(timezone.utc).strftime("%Y%m%d")
  filename = f"{prefix}_{ts}.sql"

  table_stmts: list[str] = []
  index_stmts: list[str] = []
  fk_stmts: list[str] = []
  view_stmts: list[str] = []

  for table in schema["tables"]:
    table_stmts.append(_build_create_sql(table))
    for index in table["indexes"]:
      index_stmts.append(_build_index_sql(table, index))
    for fk in table["foreign_keys"]:
      fk_stmts.extend(_build_foreign_key_sql(table, fk))

  for view in schema.get("views", []):
    definition = view["definition"].strip()
    if not definition.endswith(";"):
      definition += ";"
    view_stmts.append(definition)

  lines: list[str] = ["SET ANSI_NULLS ON;", "SET QUOTED_IDENTIFIER ON;", ""]
  for section in (table_stmts, index_stmts, fk_stmts, view_stmts):
    if not section:
      continue
    lines.extend(section)
    lines.append("")

  Path(filename).write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
  print(f"Schema dumped to {filename}")
  return filename


def parse_version(ver: str) -> tuple[int, int, int, int]:
  ver = ver.lstrip("v")
  major, minor, patch, build = [int(part) for part in ver.split(".")]
  return major, minor, patch, build


def bump_version(version: str, part: str) -> str:
  major, minor, patch, build = parse_version(version)
  match part:
    case "major":
      major += 1
      minor = 0
      patch = 0
      build = 0
    case "minor":
      minor += 1
      patch = 0
      build = 0
    case "patch":
      patch += 1
    case "build":
      build += 1
    case _:
      raise ValueError(f"Unknown part: {part}")
  return f"v{major}.{minor}.{patch}.{build}"


async def update_version(conn, part: str) -> str:
  async with conn.cursor() as cur:
    await cur.execute("SELECT element_value FROM system_config WHERE element_key='Version'")
    row = await cur.fetchone()
    if not row:
      raise RuntimeError("Version entry not found in system_config")
    current_version = row[0]

    next_version = bump_version(current_version, part)
    await cur.execute(
      "UPDATE system_config SET element_value=? WHERE element_key='Version'",
      (next_version,),
    )
  print(f"Updated Version: {current_version} -> {next_version}")
  return next_version


def commit_and_tag(version: str, schema_file: str):
  subprocess.check_call(f"git add {schema_file}", shell=True)
  subprocess.check_call(f'git commit -m "Exported DB schema for {version}"', shell=True)
  subprocess.check_call(f"git tag {version}", shell=True)
  current_branch = subprocess.check_output(
    "git rev-parse --abbrev-ref HEAD", shell=True, text=True
  ).strip()
  subprocess.check_call(f"git push origin {current_branch}", shell=True)
  subprocess.check_call("git push origin --tags", shell=True)


_GO_PATTERN = re.compile(r"^\s*GO\s*$", flags=re.IGNORECASE | re.MULTILINE)


def _iter_batches(sql: str) -> list[str]:
  return [batch for batch in _GO_PATTERN.split(sql) if batch.strip()]


async def apply_schema(conn, path: str):
  sql = Path(path).read_text(encoding="utf-8")
  batches = _iter_batches(sql)
  async with conn.cursor() as cur:
    for batch in batches:
      await cur.execute(batch)
  print("Schema applied.")


async def dump_data(conn, prefix: str = "dump_data") -> str:
  schema = await get_schema_from_registry(conn)
  data: dict[str, list[dict]] = {}
  for table in schema["tables"]:
    table_name = _qualify(table["schema"], table["name"])
    key = f"{table['schema']}.{table['name']}"
    async with conn.cursor() as cur:
      await cur.execute(f"SELECT * FROM {table_name} FOR JSON PATH")
      parts: list[str] = []
      while True:
        row = await cur.fetchone()
        if not row or not row[0]:
          break
        parts.append(row[0])
      data[key] = json.loads("".join(parts)) if parts else []
  ts = datetime.now(timezone.utc).strftime("%Y%m%d_BACKUP")
  filename = f"{prefix}_{ts}.json"
  Path(filename).write_text(
    json.dumps({"schema": schema, "data": data}, indent=2, default=str),
    encoding="utf-8",
  )
  print(f"Data dumped to {filename}")
  return filename


async def rebuild_indexes(conn):
  async with conn.cursor() as cur:
    await cur.execute("EXEC sp_MSforeachtable 'ALTER INDEX ALL ON ? REBUILD'")
  print("Reindex complete.")


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

  async def get_schema_from_registry(self, conn):
    await self.on_ready()
    return await get_schema_from_registry(conn)

  async def dump_schema_from_registry(self, conn, prefix: str = "schema"):
    await self.on_ready()
    return await dump_schema_from_registry(conn, prefix)

  async def dump_schema(self, conn, prefix: str):
    await self.on_ready()
    return await dump_schema_from_registry(conn, prefix)

  async def apply_schema(self, conn, path: str):
    await self.on_ready()
    return await apply_schema(conn, path)

  async def dump_data(self, conn, prefix: str):
    await self.on_ready()
    return await dump_data(conn, prefix)

  async def update_version(self, conn, part: str):
    await self.on_ready()
    return await update_version(conn, part)

  def commit_and_tag(self, version: str, schema_file: str):
    commit_and_tag(version, schema_file)

  async def rebuild_indexes(self, conn):
    await self.on_ready()
    return await rebuild_indexes(conn)

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
