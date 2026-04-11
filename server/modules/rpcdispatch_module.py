from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Any

from fastapi import FastAPI

from queryregistry.providers.mssql import run_json_many, run_json_one

from . import BaseModule
from .db_module import DbModule

_LIST_RPC_DOMAINS_SQL = """
  SELECT *
  FROM reflection_rpc_domains
  ORDER BY recid
  FOR JSON PATH, INCLUDE_NULL_VALUES;
"""

_LIST_RPC_SUBDOMAINS_SQL = """
  SELECT *
  FROM reflection_rpc_subdomains
  ORDER BY recid
  FOR JSON PATH, INCLUDE_NULL_VALUES;
"""

_LIST_RPC_FUNCTIONS_SQL = """
  SELECT *
  FROM reflection_rpc_functions
  ORDER BY recid
  FOR JSON PATH, INCLUDE_NULL_VALUES;
"""

_LIST_RPC_MODELS_SQL = """
  SELECT *
  FROM reflection_rpc_models
  ORDER BY recid
  FOR JSON PATH, INCLUDE_NULL_VALUES;
"""

_LIST_RPC_MODEL_FIELDS_SQL = """
  SELECT *
  FROM reflection_rpc_model_fields
  ORDER BY recid
  FOR JSON PATH, INCLUDE_NULL_VALUES;
"""

_LIST_EDT_MAPPINGS_SQL = """
  SELECT recid, element_name
  FROM reflection_db_edt_mappings
  ORDER BY recid
  FOR JSON PATH, INCLUDE_NULL_VALUES;
"""

_LIST_TABLES_SQL = """
  SELECT recid, element_schema, element_name
  FROM reflection_db_tables
  ORDER BY element_schema, element_name
  FOR JSON PATH;
"""

_LIST_COLUMNS_SQL = """
  SELECT c.tables_recid, c.element_name, c.element_nullable, c.element_default,
         c.element_max_length, c.element_is_primary_key, c.element_is_identity,
         c.element_ordinal, m.element_mssql_type
  FROM reflection_db_columns c
  JOIN reflection_db_edt_mappings m ON c.edt_recid = m.recid
  JOIN reflection_db_tables t ON c.tables_recid = t.recid
  WHERE t.element_schema = ? AND t.element_name = ?
  ORDER BY c.element_ordinal
  FOR JSON PATH;
"""

_LIST_INDEXES_SQL = """
  SELECT i.tables_recid, i.element_name, i.element_columns, i.element_is_unique
  FROM reflection_db_indexes i
  JOIN reflection_db_tables t ON i.tables_recid = t.recid
  WHERE t.element_schema = ? AND t.element_name = ?
  ORDER BY i.element_name
  FOR JSON PATH;
"""

_LIST_FOREIGN_KEYS_SQL = """
  SELECT fk.tables_recid, fk.element_column_name, fk.referenced_tables_recid,
         fk.element_referenced_column
  FROM reflection_db_foreign_keys fk
  JOIN reflection_db_tables t ON fk.tables_recid = t.recid
  WHERE t.element_schema = ? AND t.element_name = ?
  ORDER BY fk.element_column_name
  FOR JSON PATH;
"""

_LIST_VIEWS_SQL = """
  SELECT element_schema, element_name, element_definition
  FROM reflection_db_views
  ORDER BY element_schema, element_name
  FOR JSON PATH;
"""

_GET_VERSION_SQL = """
  SELECT element_value
  FROM system_config
  WHERE element_key='Version'
  FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
"""

_ALL_COLUMNS_SQL = """
  SELECT c.tables_recid, c.element_name, c.element_nullable, c.element_default,
         c.element_max_length, c.element_is_primary_key, c.element_is_identity,
         c.element_ordinal, m.element_mssql_type
  FROM reflection_db_columns c
  JOIN reflection_db_edt_mappings m ON c.edt_recid = m.recid
  ORDER BY c.tables_recid, c.element_ordinal
  FOR JSON PATH;
"""

_ALL_INDEXES_SQL = """
  SELECT i.tables_recid, i.element_name, i.element_columns, i.element_is_unique
  FROM reflection_db_indexes i
  ORDER BY i.tables_recid, i.element_name
  FOR JSON PATH;
"""

_ALL_FOREIGN_KEYS_SQL = """
  SELECT fk.tables_recid, fk.element_column_name, fk.referenced_tables_recid,
         fk.element_referenced_column
  FROM reflection_db_foreign_keys fk
  ORDER BY fk.tables_recid, fk.element_column_name
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
  recid: int
  guid: str
  name: str
  version: int
  module_attr: str
  method_name: str
  request_model_guid: str | None
  response_model_guid: str | None


@dataclass
class SubdomainEntry:
  recid: int
  guid: str
  name: str
  entitlement_mask: int
  functions: dict[tuple[str, int], FunctionEntry] = field(default_factory=dict)


@dataclass
class DomainEntry:
  recid: int
  guid: str
  name: str
  required_role: str | None
  is_auth_exempt: bool
  is_public: bool
  is_discord: bool
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
        recid=int(row.get("recid")),
        guid=str(row.get("element_guid")),
        name=str(row.get("element_name")),
        required_role=row.get("element_required_role"),
        is_auth_exempt=bool(row.get("element_is_auth_exempt")),
        is_public=bool(row.get("element_is_public")),
        is_discord=bool(row.get("element_is_discord")),
      )
      domains[entry.name] = entry
      by_domain_guid[entry.guid] = entry

    for row in subdomain_rows:
      domain_entry = by_domain_guid.get(str(row.get("domains_guid")))
      if domain_entry is None:
        continue
      entry = SubdomainEntry(
        recid=int(row.get("recid")),
        guid=str(row.get("element_guid")),
        name=str(row.get("element_name")),
        entitlement_mask=int(row.get("element_entitlement_mask") or 0),
      )
      domain_entry.subdomains[entry.name] = entry
      by_subdomain_guid[entry.guid] = entry

    for row in function_rows:
      subdomain_entry = by_subdomain_guid.get(str(row.get("subdomains_guid")))
      if subdomain_entry is None:
        continue
      entry = FunctionEntry(
        recid=int(row.get("recid")),
        guid=str(row.get("element_guid")),
        name=str(row.get("element_name")),
        version=int(row.get("element_version") or 1),
        module_attr=str(row.get("element_module_attr")),
        method_name=str(row.get("element_method_name")),
        request_model_guid=row.get("element_request_model_guid"),
        response_model_guid=row.get("element_response_model_guid"),
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
