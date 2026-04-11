"""Database CLI module exposing management helpers."""

import ast
import json
import logging
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

from . import BaseModule
from .db_module import DbModule
from .env_module import EnvModule


def _quote(name: str) -> str:
  return "[" + name.replace("]", "]]" ) + "]"


def _qualify(schema: str, name: str) -> str:
  return f"{_quote(schema)}.{_quote(name)}"


async def _load_full_schema() -> dict[str, Any]:
  tables = await run_json_many(
    """
    SELECT recid, element_schema, element_name
    FROM reflection_db_tables
    ORDER BY element_schema, element_name
    FOR JSON PATH;
    """
  )
  columns = await run_json_many(
    """
    SELECT c.tables_recid, c.element_name, c.element_nullable, c.element_default,
           c.element_max_length, c.element_is_primary_key, c.element_is_identity,
           c.element_ordinal, m.element_mssql_type
    FROM reflection_db_columns c
    JOIN reflection_db_edt_mappings m ON c.edt_recid = m.recid
    ORDER BY c.tables_recid, c.element_ordinal
    FOR JSON PATH;
    """
  )
  indexes = await run_json_many(
    """
    SELECT i.tables_recid, i.element_name, i.element_columns, i.element_is_unique
    FROM reflection_db_indexes i
    ORDER BY i.tables_recid, i.element_name
    FOR JSON PATH;
    """
  )
  foreign_keys = await run_json_many(
    """
    SELECT fk.tables_recid, fk.element_column_name, fk.referenced_tables_recid,
           fk.element_referenced_column
    FROM reflection_db_foreign_keys fk
    ORDER BY fk.tables_recid, fk.element_column_name
    FOR JSON PATH;
    """
  )
  views = await run_json_many(
    """
    SELECT element_schema, element_name, element_definition
    FROM reflection_db_views
    ORDER BY element_schema, element_name
    FOR JSON PATH;
    """
  )
  return {
    "tables": tables or [],
    "columns": columns or [],
    "indexes": indexes or [],
    "foreign_keys": foreign_keys or [],
    "views": views or [],
  }


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


def commit_and_tag(version: str, files: list[str]):
  for file in files:
    subprocess.check_call(f"git add {file}", shell=True)
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


def _sql_literal(value: Any) -> str:
  if value is None:
    return "NULL"
  if isinstance(value, bool):
    return "1" if value else "0"
  if isinstance(value, (int, float)):
    return str(value)
  text = str(value).replace("'", "''")
  return f"'{text}'"


class DatabaseCliModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self._queryregistry_root = Path(__file__).resolve().parents[2] / "queryregistry"

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    env: EnvModule = self.app.state.env
    await env.on_ready()
    logging.info("[DatabaseCli] module ready")
    self.mark_ready()

  async def shutdown(self):
    self.db = None

  async def list_tables(self):
    await self.on_ready()
    rows = await run_json_many(
      """
      SELECT recid, element_schema, element_name
      FROM reflection_db_tables
      ORDER BY element_schema, element_name
      FOR JSON PATH;
      """
    )
    return [f"{row['element_schema']}.{row['element_name']}" for row in rows]

  async def get_schema_from_registry(self):
    await self.on_ready()
    payload = await _load_full_schema()

    table_rows = payload.get("tables", [])
    tables: dict[int, dict] = {}
    for row in table_rows:
      table_recid = int(row["recid"])
      tables[table_recid] = {
        "recid": table_recid,
        "schema": row["element_schema"],
        "name": row["element_name"],
        "columns": [],
        "primary_key": None,
        "unique_constraints": [],
        "check_constraints": [],
        "foreign_keys": [],
        "indexes": [],
      }

    for row in payload.get("columns", []):
      tables_recid = int(row["tables_recid"])
      table = tables.get(tables_recid)
      if not table:
        continue
      table["columns"].append(
        {
          "name": row["element_name"],
          "data_type": row["element_mssql_type"],
          "max_length": row.get("element_max_length"),
          "precision": None,
          "scale": None,
          "nullable": bool(row["element_nullable"]),
          "default": row.get("element_default"),
          "identity": bool(row["element_is_identity"]),
          "identity_seed": 1,
          "identity_increment": 1,
          "rowguidcol": False,
          "computed": None,
          "computed_persisted": False,
          "collation": None,
          "is_primary_key": bool(row["element_is_primary_key"]),
          "ordinal": int(row.get("element_ordinal") or 0),
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

    for row in payload.get("indexes", []):
      tables_recid = int(row["tables_recid"])
      table = tables.get(tables_recid)
      if not table:
        continue
      key_columns = [_quote(col.strip()) for col in (row.get("element_columns") or "").split(",") if col.strip()]
      table["indexes"].append(
        {
          "name": row["element_name"],
          "is_unique": bool(row["element_is_unique"]),
          "type_desc": "",
          "has_filter": False,
          "filter_definition": None,
          "key_columns": key_columns,
          "included_columns": [],
        }
      )

    view_rows = payload.get("views", [])
    views = [
      {
        "schema": row["element_schema"],
        "name": row["element_name"],
        "definition": row.get("element_definition", ""),
      }
      for row in view_rows
    ]

    for row in payload.get("foreign_keys", []):
      tables_recid = int(row["tables_recid"])
      table = tables.get(tables_recid)
      ref_table = tables.get(int(row["referenced_tables_recid"]))
      if not table or not ref_table:
        continue
      source_column = row["element_column_name"]
      ref_column = row["element_referenced_column"]
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

  async def dump_schema_from_registry(self, prefix: str = "schema"):
    await self.on_ready()
    schema = await self.get_schema_from_registry()
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

  async def dump_seed_from_registry(self, prefix: str = "seed"):
    await self.on_ready()
    if not self.db:
      raise RuntimeError("DatabaseCliModule missing DbModule dependency")

    schema = await self.get_schema_from_registry()
    edt_rows = await run_json_many("SELECT * FROM [dbo].[system_edt_mappings] FOR JSON PATH;")
    view_rows = await run_json_many("SELECT * FROM [dbo].[system_schema_views] FOR JSON PATH;")
    edt_name_by_mssql_type = {
      str(row.get("element_mssql_type") or ""): str(row.get("element_name") or "")
      for row in edt_rows
      if row.get("element_mssql_type") and row.get("element_name")
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    filename = f"{prefix}_{ts}.sql"

    tables = schema.get("tables", [])
    table_lookup = {(table["schema"], table["name"]): table for table in tables}

    table_insert_values: list[str] = []
    column_insert_values: list[str] = []
    index_insert_values: list[str] = []
    fk_insert_values: list[str] = []

    for table in tables:
      table_insert_values.append(
        f"({_sql_literal(table['name'])}, {_sql_literal(table['schema'])})"
      )

      columns = sorted(table.get("columns", []), key=lambda row: int(row.get("ordinal", 0)))
      for ordinal, column in enumerate(columns, start=1):
        data_type = str(column.get("data_type") or "")
        edt_name = edt_name_by_mssql_type.get(data_type)
        if not edt_name:
          edt_name = data_type.split("(", 1)[0].strip().upper()
        table_recid_sql = (
          "(SELECT recid FROM system_schema_tables "
          f"WHERE element_name = {_sql_literal(table['name'])} "
          f"AND element_schema = {_sql_literal(table['schema'])})"
        )
        edt_recid_sql = (
          "(SELECT recid FROM system_edt_mappings "
          f"WHERE element_name = {_sql_literal(edt_name)})"
        )
        column_insert_values.append(
          "("
          f"{table_recid_sql}, "
          f"{edt_recid_sql}, "
          f"{_sql_literal(column.get('name'))}, "
          f"{_sql_literal(ordinal)}, "
          f"{_sql_literal(bool(column.get('nullable', True)))}, "
          f"{_sql_literal(column.get('default'))}, "
          f"{_sql_literal(column.get('max_length'))}, "
          f"{_sql_literal(bool(column.get('is_primary_key', False)))}, "
          f"{_sql_literal(bool(column.get('identity', False)))}"
          ")"
        )

      for index in table.get("indexes", []):
        table_recid_sql = (
          "(SELECT recid FROM system_schema_tables "
          f"WHERE element_name = {_sql_literal(table['name'])} "
          f"AND element_schema = {_sql_literal(table['schema'])})"
        )
        element_columns = ", ".join(col.strip("[]") for col in index.get("key_columns", []))
        index_insert_values.append(
          "("
          f"{table_recid_sql}, "
          f"{_sql_literal(index.get('name'))}, "
          f"{_sql_literal(element_columns)}, "
          f"{_sql_literal(bool(index.get('is_unique', False)))}"
          ")"
        )

      for fk in table.get("foreign_keys", []):
        ref_table = table_lookup.get((fk.get("ref_schema"), fk.get("ref_table")))
        if not ref_table:
          continue
        table_recid_sql = (
          "(SELECT recid FROM system_schema_tables "
          f"WHERE element_name = {_sql_literal(table['name'])} "
          f"AND element_schema = {_sql_literal(table['schema'])})"
        )
        ref_table_recid_sql = (
          "(SELECT recid FROM system_schema_tables "
          f"WHERE element_name = {_sql_literal(ref_table['name'])} "
          f"AND element_schema = {_sql_literal(ref_table['schema'])})"
        )
        fk_insert_values.append(
          "("
          f"{table_recid_sql}, "
          f"{_sql_literal((fk.get('columns') or [''])[0].strip('[]'))}, "
          f"{ref_table_recid_sql}, "
          f"{_sql_literal((fk.get('ref_columns') or [''])[0].strip('[]'))}"
          ")"
        )

    lines: list[str] = ["SET NOCOUNT ON;", ""]

    if edt_rows:
      edt_values = []
      for row in edt_rows:
        edt_values.append(
          "("
          f"{_sql_literal(row.get('element_name'))}, "
          f"{_sql_literal(row.get('element_mssql_type'))}, "
          f"{_sql_literal(row.get('element_postgresql_type'))}, "
          f"{_sql_literal(row.get('element_mysql_type'))}, "
          f"{_sql_literal(row.get('element_python_type'))}, "
          f"{_sql_literal(row.get('element_odbc_type_code'))}, "
          f"{_sql_literal(row.get('element_max_length'))}, "
          f"{_sql_literal(row.get('element_notes'))}"
          ")"
        )
      lines.extend(
        [
          "INSERT INTO system_edt_mappings (",
          "  element_name, element_mssql_type, element_postgresql_type, element_mysql_type,",
          "  element_python_type, element_odbc_type_code, element_max_length, element_notes",
          ") VALUES",
          "  " + ",\n  ".join(edt_values) + ";",
          "",
        ]
      )

    if table_insert_values:
      lines.extend(
        [
          "INSERT INTO system_schema_tables (element_name, element_schema) VALUES",
          "  " + ",\n  ".join(table_insert_values) + ";",
          "",
        ]
      )

    if column_insert_values:
      lines.extend(
        [
          "INSERT INTO system_schema_columns (",
          "  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,",
          "  element_default, element_max_length, element_is_primary_key, element_is_identity",
          ") VALUES",
          "  " + ",\n  ".join(column_insert_values) + ";",
          "",
        ]
      )

    if index_insert_values:
      lines.extend(
        [
          "INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique) VALUES",
          "  " + ",\n  ".join(index_insert_values) + ";",
          "",
        ]
      )

    if fk_insert_values:
      lines.extend(
        [
          "INSERT INTO system_schema_foreign_keys (",
          "  tables_recid, element_column_name, referenced_tables_recid, element_referenced_column",
          ") VALUES",
          "  " + ",\n  ".join(fk_insert_values) + ";",
          "",
        ]
      )

    if view_rows:
      view_values = []
      for row in view_rows:
        view_values.append(
          "("
          f"{_sql_literal(row.get('element_name'))}, "
          f"{_sql_literal(row.get('element_schema'))}, "
          f"{_sql_literal(row.get('element_definition'))}"
          ")"
        )
      lines.extend(
        [
          "INSERT INTO system_schema_views (element_name, element_schema, element_definition) VALUES",
          "  " + ",\n  ".join(view_values) + ";",
          "",
        ]
      )

    Path(filename).write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Seed dumped to {filename}")
    return filename

  async def apply_schema(self, path: str = ""):
    await self.on_ready()
    if not self.db:
      raise RuntimeError("DatabaseCliModule missing DbModule dependency")
    sql = Path(path).read_text(encoding="utf-8")
    batches = _iter_batches(sql)
    for batch in batches:
      await run_exec(batch)
    print("Schema applied.")

  async def dump_data(self, prefix: str = "dump_data"):
    await self.on_ready()
    if not self.db:
      raise RuntimeError("DatabaseCliModule missing DbModule dependency")
    schema = await self.get_schema_from_registry()
    data: dict[str, list[dict]] = {}
    for table in schema["tables"]:
      key = f"{table['schema']}.{table['name']}"
      table_rows = await run_json_many(
        f"SELECT * FROM {_qualify(table['schema'], table['name'])} FOR JSON PATH;"
      )
      data[key] = table_rows
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_BACKUP")
    filename = f"{prefix}_{ts}.json"
    Path(filename).write_text(
      json.dumps({"schema": schema, "data": data}, indent=2, default=str),
      encoding="utf-8",
    )
    print(f"Data dumped to {filename}")
    return filename

  async def update_version(self, part: str = ""):
    await self.on_ready()
    if not self.db:
      raise RuntimeError("DatabaseCliModule missing DbModule dependency")
    version_payload = await run_json_one(
      """
      SELECT element_value
      FROM system_config
      WHERE element_key='Version'
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
      """
    ) or {}
    current_version = version_payload.get("element_value")
    if not current_version:
      raise RuntimeError("Version entry not found in system_config")

    next_version = bump_version(current_version, part)
    await run_exec("UPDATE system_config SET element_value=? WHERE element_key='Version';", (next_version,))
    print(f"Updated Version: {current_version} -> {next_version}")
    return next_version

  def commit_and_tag(self, version: str, files: list[str]):
    commit_and_tag(version, files)

  async def rebuild_indexes(self):
    await self.on_ready()
    if not self.db:
      raise RuntimeError("DatabaseCliModule missing DbModule dependency")
    await run_exec("EXEC sp_MSforeachtable 'ALTER INDEX ALL ON ? REBUILD'")
    print("Reindex complete.")

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
