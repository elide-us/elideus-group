from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Any

from fastapi import FastAPI

from queryregistry.providers.mssql import run_json_many, run_json_one

from . import BaseModule
from .db_module import DbModule

_LIST_RPC_DOMAINS_SQL = """
  SELECT
    key_guid,
    pub_name,
    pub_description,
    ref_required_role_guid,
    pub_is_active
  FROM system_objects_rpc_domains
  ORDER BY pub_name
  FOR JSON PATH, INCLUDE_NULL_VALUES;
"""

_LIST_RPC_SUBDOMAINS_SQL = """
  SELECT
    s.key_guid,
    s.pub_name,
    s.pub_description,
    s.ref_domain_guid,
    d.pub_name AS domain_name,
    s.ref_required_entitlement_guid,
    s.pub_is_active
  FROM system_objects_rpc_subdomains s
  JOIN system_objects_rpc_domains d ON s.ref_domain_guid = d.key_guid
  ORDER BY d.pub_name, s.pub_name
  FOR JSON PATH, INCLUDE_NULL_VALUES;
"""

_LIST_RPC_FUNCTIONS_SQL = """
  SELECT
    f.key_guid,
    f.pub_name,
    f.pub_version,
    f.pub_description,
    f.ref_subdomain_guid,
    s.pub_name AS subdomain_name,
    d.pub_name AS domain_name,
    f.ref_method_guid,
    m.pub_name AS method_name,
    mod.pub_state_attr AS module_attr,
    f.ref_required_role_guid,
    f.ref_required_entitlement_guid,
    f.pub_is_active
  FROM system_objects_rpc_functions f
  JOIN system_objects_rpc_subdomains s ON f.ref_subdomain_guid = s.key_guid
  JOIN system_objects_rpc_domains d ON s.ref_domain_guid = d.key_guid
  JOIN system_objects_module_methods m ON f.ref_method_guid = m.key_guid
  JOIN system_objects_modules mod ON m.ref_module_guid = mod.key_guid
  ORDER BY d.pub_name, s.pub_name, f.pub_name
  FOR JSON PATH, INCLUDE_NULL_VALUES;
"""

_LIST_RPC_MODELS_SQL = """
  SELECT
    key_guid,
    pub_name,
    pub_description,
    pub_version,
    ref_parent_model_guid
  FROM system_objects_rpc_models
  ORDER BY pub_name
  FOR JSON PATH, INCLUDE_NULL_VALUES;
"""

_LIST_RPC_MODEL_FIELDS_SQL = """
  SELECT
    f.key_guid,
    f.ref_model_guid,
    m.pub_name AS model_name,
    f.pub_name,
    f.pub_ordinal,
    t.pub_name AS type_name,
    nm.pub_name AS nested_model_name,
    f.pub_is_nullable,
    f.pub_is_list,
    f.pub_default_value,
    f.pub_max_length,
    f.pub_description
  FROM system_objects_rpc_model_fields f
  JOIN system_objects_rpc_models m ON f.ref_model_guid = m.key_guid
  LEFT JOIN system_objects_types t ON f.ref_type_guid = t.key_guid
  LEFT JOIN system_objects_rpc_models nm ON f.ref_nested_model_guid = nm.key_guid
  ORDER BY m.pub_name, f.pub_ordinal
  FOR JSON PATH, INCLUDE_NULL_VALUES;
"""

_LIST_EDT_MAPPINGS_SQL = """
  SELECT pub_name AS element_name, pub_mssql_type, pub_python_type, pub_typescript_type
  FROM system_objects_types
  ORDER BY pub_name
  FOR JSON PATH, INCLUDE_NULL_VALUES;
"""

_LIST_TABLES_SQL = """
  SELECT pub_schema AS element_schema, pub_name AS element_name
  FROM system_objects_database_tables
  ORDER BY pub_schema, pub_name
  FOR JSON PATH;
"""

_LIST_COLUMNS_SQL = """
  SELECT
    c.ref_table_guid AS table_guid,
    c.pub_name AS element_name,
    c.pub_is_nullable AS element_nullable,
    c.pub_default AS element_default,
    c.pub_max_length AS element_max_length,
    c.pub_is_primary_key AS element_is_primary_key,
    c.pub_is_identity AS element_is_identity,
    c.pub_ordinal AS element_ordinal,
    t.pub_mssql_type AS element_mssql_type
  FROM system_objects_database_columns c
  JOIN system_objects_types t ON c.ref_type_guid = t.key_guid
  JOIN system_objects_database_tables tbl ON c.ref_table_guid = tbl.key_guid
  WHERE tbl.pub_schema = ? AND tbl.pub_name = ?
  ORDER BY c.pub_ordinal
  FOR JSON PATH;
"""

_LIST_INDEXES_SQL = """
  SELECT
    i.ref_table_guid AS table_guid,
    i.pub_name AS element_name,
    i.pub_columns AS element_columns,
    i.pub_is_unique AS element_is_unique
  FROM system_objects_database_indexes i
  JOIN system_objects_database_tables t ON i.ref_table_guid = t.key_guid
  WHERE t.pub_schema = ? AND t.pub_name = ?
  ORDER BY i.pub_name
  FOR JSON PATH;
"""

_LIST_FOREIGN_KEYS_SQL = """
  SELECT
    fk.ref_table_guid AS table_guid,
    src_col.pub_name AS element_column_name,
    fk.ref_referenced_table_guid AS referenced_table_guid,
    ref_col.pub_name AS element_referenced_column
  FROM system_objects_database_constraints fk
  JOIN system_objects_database_tables t ON fk.ref_table_guid = t.key_guid
  JOIN system_objects_database_columns src_col ON fk.ref_column_guid = src_col.key_guid
  JOIN system_objects_database_columns ref_col ON fk.ref_referenced_column_guid = ref_col.key_guid
  WHERE t.pub_schema = ? AND t.pub_name = ?
  ORDER BY src_col.pub_name
  FOR JSON PATH;
"""

_LIST_VIEWS_SQL = """
  SELECT TABLE_SCHEMA AS element_schema, TABLE_NAME AS element_name,
         VIEW_DEFINITION AS element_definition
  FROM INFORMATION_SCHEMA.VIEWS
  ORDER BY TABLE_SCHEMA, TABLE_NAME
  FOR JSON PATH;
"""

_GET_VERSION_SQL = """
  SELECT element_value
  FROM system_config
  WHERE element_key='Version'
  FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
"""

_ALL_COLUMNS_SQL = """
  SELECT
    c.ref_table_guid AS table_guid,
    c.pub_name AS element_name,
    c.pub_is_nullable AS element_nullable,
    c.pub_default AS element_default,
    c.pub_max_length AS element_max_length,
    c.pub_is_primary_key AS element_is_primary_key,
    c.pub_is_identity AS element_is_identity,
    c.pub_ordinal AS element_ordinal,
    t.pub_mssql_type AS element_mssql_type
  FROM system_objects_database_columns c
  JOIN system_objects_types t ON c.ref_type_guid = t.key_guid
  ORDER BY c.ref_table_guid, c.pub_ordinal
  FOR JSON PATH;
"""

_ALL_INDEXES_SQL = """
  SELECT
    i.ref_table_guid AS table_guid,
    i.pub_name AS element_name,
    i.pub_columns AS element_columns,
    i.pub_is_unique AS element_is_unique
  FROM system_objects_database_indexes i
  ORDER BY i.ref_table_guid, i.pub_name
  FOR JSON PATH;
"""

_ALL_FOREIGN_KEYS_SQL = """
  SELECT
    fk.ref_table_guid AS table_guid,
    src_col.pub_name AS element_column_name,
    fk.ref_referenced_table_guid AS referenced_table_guid,
    ref_col.pub_name AS element_referenced_column
  FROM system_objects_database_constraints fk
  JOIN system_objects_database_columns src_col ON fk.ref_column_guid = src_col.key_guid
  JOIN system_objects_database_columns ref_col ON fk.ref_referenced_column_guid = ref_col.key_guid
  ORDER BY fk.ref_table_guid, src_col.pub_name
  FOR JSON PATH;
"""

_QUOTED_INFO_SCHEMA_VIEWS = frozenset({
  "TABLES",
  "COLUMNS",
  "KEY_COLUMN_USAGE",
  "TABLE_CONSTRAINTS",
  "REFERENTIAL_CONSTRAINTS",
  "CHECK_CONSTRAINTS",
  "VIEWS",
  "ROUTINES",
  "PARAMETERS",
  "SCHEMATA",
  "DOMAINS",
})


@dataclass
class FunctionEntry:
  guid: str
  name: str
  version: int
  module_attr: str
  method_name: str


@dataclass
class SubdomainEntry:
  guid: str
  name: str
  domain_guid: str
  functions: dict[tuple[str, int], FunctionEntry] = field(default_factory=dict)


@dataclass
class DomainEntry:
  guid: str
  name: str
  required_role_guid: str | None
  is_active: bool
  subdomains: dict[str, SubdomainEntry] = field(default_factory=dict)


class RpcdispatchModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self._domains: dict[str, DomainEntry] = {}

  @staticmethod
  def _quote_ident(identifier: str) -> str:
    return "[" + identifier.replace("]", "]]" ) + "]"

  @staticmethod
  def _as_list(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
      return []
    if isinstance(payload, list):
      return [dict(row) if isinstance(row, dict) else row for row in payload]
    if isinstance(payload, dict):
      return [payload]
    return []

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    await self.reload()
    self.mark_ready()

  async def shutdown(self):
    self._domains.clear()
    self.db = None

  async def reload(self) -> None:
    if self.db is None:
      raise RuntimeError("rpcdispatch module requires db module")
    domain_rows = await self.list_domains()
    subdomain_rows = await self.list_subdomains()
    function_rows = await self.list_functions()

    domains: dict[str, DomainEntry] = {}
    by_domain_guid: dict[str, DomainEntry] = {}
    by_subdomain_guid: dict[str, SubdomainEntry] = {}

    for row in domain_rows:
      entry = DomainEntry(
        guid=str(row.get("key_guid", "")),
        name=str(row.get("pub_name", "")),
        required_role_guid=row.get("ref_required_role_guid"),
        is_active=bool(row.get("pub_is_active", True)),
      )
      domains[entry.name] = entry
      by_domain_guid[entry.guid] = entry

    for row in subdomain_rows:
      domain_entry = by_domain_guid.get(str(row.get("ref_domain_guid", "")))
      if domain_entry is None:
        continue
      entry = SubdomainEntry(
        guid=str(row.get("key_guid", "")),
        name=str(row.get("pub_name", "")),
        domain_guid=str(row.get("ref_domain_guid", "")),
      )
      domain_entry.subdomains[entry.name] = entry
      by_subdomain_guid[entry.guid] = entry

    for row in function_rows:
      subdomain_entry = by_subdomain_guid.get(str(row.get("ref_subdomain_guid", "")))
      if subdomain_entry is None:
        continue
      entry = FunctionEntry(
        guid=str(row.get("key_guid", "")),
        name=str(row.get("pub_name", "")),
        version=int(row.get("pub_version") or 1),
        module_attr=str(row.get("module_attr", "")),
        method_name=str(row.get("method_name", "")),
      )
      subdomain_entry.functions[(entry.name, entry.version)] = entry

    self._domains = domains
    logging.info(
      "[rpcdispatch_startup] loaded domains=%d subdomains=%d functions=%d",
      len(domain_rows),
      len(subdomain_rows),
      len(function_rows),
    )

  async def get_domain(self, name: str) -> DomainEntry | None:
    return self._domains.get(name)

  async def get_subdomain(self, domain: str, subdomain: str) -> SubdomainEntry | None:
    domain_entry = self._domains.get(domain)
    if domain_entry is None:
      return None
    return domain_entry.subdomains.get(subdomain)

  async def get_function(
    self,
    domain: str,
    subdomain: str,
    function: str,
    version: int,
  ) -> FunctionEntry | None:
    subdomain_entry = await self.get_subdomain(domain, subdomain)
    if subdomain_entry is None:
      return None
    return subdomain_entry.functions.get((function, version))

  async def list_domains(self) -> list[dict[str, Any]]:
    return self._as_list(await run_json_many(_LIST_RPC_DOMAINS_SQL))

  async def list_subdomains(self) -> list[dict[str, Any]]:
    return self._as_list(await run_json_many(_LIST_RPC_SUBDOMAINS_SQL))

  async def list_functions(self) -> list[dict[str, Any]]:
    return self._as_list(await run_json_many(_LIST_RPC_FUNCTIONS_SQL))

  async def list_models(self) -> list[dict[str, Any]]:
    return self._as_list(await run_json_many(_LIST_RPC_MODELS_SQL))

  async def list_model_fields(self) -> list[dict[str, Any]]:
    return self._as_list(await run_json_many(_LIST_RPC_MODEL_FIELDS_SQL))

  async def list_edt_mappings(self) -> list[dict[str, Any]]:
    return self._as_list(await run_json_many(_LIST_EDT_MAPPINGS_SQL))

  async def list_tables(self) -> list[dict[str, Any]]:
    return self._as_list(await run_json_many(_LIST_TABLES_SQL))

  async def describe_table(self, table_name: str, table_schema: str) -> dict[str, Any]:
    args = (table_schema, table_name)
    columns = await run_json_many(_LIST_COLUMNS_SQL, args)
    indexes = await run_json_many(_LIST_INDEXES_SQL, args)
    foreign_keys = await run_json_many(_LIST_FOREIGN_KEYS_SQL, args)
    return {
      "columns": self._as_list(columns),
      "indexes": self._as_list(indexes),
      "foreign_keys": self._as_list(foreign_keys),
    }

  async def list_views(self) -> list[dict[str, Any]]:
    return self._as_list(await run_json_many(_LIST_VIEWS_SQL))

  async def get_full_schema(self) -> Any:
    tables = await run_json_many(_LIST_TABLES_SQL)
    columns = await run_json_many(_ALL_COLUMNS_SQL)
    indexes = await run_json_many(_ALL_INDEXES_SQL)
    foreign_keys = await run_json_many(_ALL_FOREIGN_KEYS_SQL)
    views = await run_json_many(_LIST_VIEWS_SQL)
    return {
      "tables": self._as_list(tables),
      "columns": self._as_list(columns),
      "indexes": self._as_list(indexes),
      "foreign_keys": self._as_list(foreign_keys),
      "views": self._as_list(views),
    }

  async def get_schema_version(self) -> Any:
    data = await run_json_one(_GET_VERSION_SQL)
    if isinstance(data, dict):
      return data.get("element_value", data)
    return data

  async def dump_table(self, table_name: str, table_schema: str, max_rows: int) -> dict[str, Any]:
    safe_schema = self._quote_ident(table_schema)
    safe_table = self._quote_ident(table_name)
    rows = await run_json_many(f"SELECT * FROM {safe_schema}.{safe_table} FOR JSON PATH;")
    all_rows = self._as_list(rows)
    total_rows = len(all_rows)
    bounded_rows = all_rows[:max_rows]
    return {
      "rows": bounded_rows,
      "truncated": total_rows > max_rows,
      "total_rows": total_rows,
    }

  async def query_info_schema(
    self,
    view_name: str,
    filter_column: str | None,
    filter_value: str | None,
  ) -> list[dict[str, Any]]:
    upper_view = view_name.upper()
    if upper_view not in _QUOTED_INFO_SCHEMA_VIEWS:
      raise ValueError(f"Unsupported INFORMATION_SCHEMA view: {view_name}")

    view_ident = self._quote_ident(upper_view)
    sql = f"SELECT * FROM INFORMATION_SCHEMA.{view_ident}"
    params: tuple[str, ...] = ()

    if filter_column is not None and filter_value is not None:
      col_ident = self._quote_ident(filter_column)
      sql += f" WHERE {col_ident} = ?"
      params = (filter_value,)

    sql += " FOR JSON PATH;"
    rows = await run_json_many(sql, params)
    return self._as_list(rows)

  async def list_rpc_endpoints(self) -> list[str]:
    from rpc import HANDLERS

    return sorted(HANDLERS.keys())
