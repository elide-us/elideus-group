from __future__ import annotations

from dataclasses import dataclass, field
import importlib
import logging
from typing import Any

from fastapi import FastAPI

from queryregistry.handler import HANDLERS as QR_HANDLERS
from queryregistry.reflection.data import dump_table_request, get_version_request, query_info_schema_request
from queryregistry.reflection.data.models import DumpTableParams, QueryInfoSchemaParams
from queryregistry.reflection.schema import (
  get_full_schema_request,
  list_columns_request,
  list_foreign_keys_request,
  list_indexes_request,
  list_tables_request,
  list_views_request,
)
from queryregistry.reflection.schema.models import TableParams
from queryregistry.rpcdispatch.domains import list_domains_request
from queryregistry.rpcdispatch.functions import list_functions_request
from queryregistry.rpcdispatch.model_fields import list_model_fields_request
from queryregistry.rpcdispatch.models import list_models_request
from queryregistry.rpcdispatch.subdomains import list_subdomains_request

from . import BaseModule
from .db_module import DbModule


@dataclass
class FunctionEntry:
  recid: int
  name: str
  version: int
  module_attr: str
  method_name: str
  request_model_recid: int | None
  response_model_recid: int | None


@dataclass
class SubdomainEntry:
  recid: int
  name: str
  entitlement_mask: int
  functions: dict[tuple[str, int], FunctionEntry] = field(default_factory=dict)


@dataclass
class DomainEntry:
  recid: int
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
  def _extract_payload(response: Any) -> Any:
    if hasattr(response, "payload"):
      return response.payload
    return response

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
    domain_rows = (await self.db.run(list_domains_request())).rows
    subdomain_rows = (await self.db.run(list_subdomains_request())).rows
    function_rows = (await self.db.run(list_functions_request())).rows

    domains: dict[str, DomainEntry] = {}
    by_domain_recid: dict[int, DomainEntry] = {}
    by_subdomain_recid: dict[int, SubdomainEntry] = {}

    for row in domain_rows:
      entry = DomainEntry(
        recid=int(row.get("recid")),
        name=str(row.get("element_name")),
        required_role=row.get("element_required_role"),
        is_auth_exempt=bool(row.get("element_is_auth_exempt")),
        is_public=bool(row.get("element_is_public")),
        is_discord=bool(row.get("element_is_discord")),
      )
      domains[entry.name] = entry
      by_domain_recid[entry.recid] = entry

    for row in subdomain_rows:
      domain_entry = by_domain_recid.get(int(row.get("domains_recid")))
      if domain_entry is None:
        continue
      entry = SubdomainEntry(
        recid=int(row.get("recid")),
        name=str(row.get("element_name")),
        entitlement_mask=int(row.get("element_entitlement_mask") or 0),
      )
      domain_entry.subdomains[entry.name] = entry
      by_subdomain_recid[entry.recid] = entry

    for row in function_rows:
      subdomain_entry = by_subdomain_recid.get(int(row.get("subdomains_recid")))
      if subdomain_entry is None:
        continue
      entry = FunctionEntry(
        recid=int(row.get("recid")),
        name=str(row.get("element_name")),
        version=int(row.get("element_version") or 1),
        module_attr=str(row.get("element_module_attr")),
        method_name=str(row.get("element_method_name")),
        request_model_recid=row.get("element_request_model_recid"),
        response_model_recid=row.get("element_response_model_recid"),
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

  async def list_domains(self) -> list[dict[str, Any]] | dict[str, Any]:
    if self.db is None:
      raise RuntimeError("rpcdispatch module requires db module")
    result = await self.db.run(list_domains_request())
    rows = result.rows or []
    if rows:
      return [dict(row) for row in rows]

    discovered: dict[str, Any] = {}
    for domain, domain_handler in QR_HANDLERS.items():
      try:
        domain_module = importlib.import_module(domain_handler.__module__)
        subdomain_handlers = getattr(domain_module, "HANDLERS")
        if not isinstance(subdomain_handlers, dict):
          raise TypeError("HANDLERS is not a dict")
        domain_entry: dict[str, Any] = {}
        for subdomain, subdomain_handler in subdomain_handlers.items():
          subdomain_module = importlib.import_module(subdomain_handler.__module__)
          dispatchers = getattr(subdomain_module, "DISPATCHERS")
          if not isinstance(dispatchers, dict):
            raise TypeError("DISPATCHERS is not a dict")
          operations = [f"{operation}:{version}" for operation, version in dispatchers.keys()]
          domain_entry[str(subdomain)] = sorted(operations)
        discovered[domain] = domain_entry
      except Exception as exc:
        discovered[domain] = {"error": str(exc)}
    return discovered

  async def list_subdomains(self) -> list[dict[str, Any]]:
    if self.db is None:
      raise RuntimeError("rpcdispatch module requires db module")
    result = await self.db.run(list_subdomains_request())
    return [dict(row) for row in (result.rows or [])]

  async def list_functions(self) -> list[dict[str, Any]]:
    if self.db is None:
      raise RuntimeError("rpcdispatch module requires db module")
    result = await self.db.run(list_functions_request())
    return [dict(row) for row in (result.rows or [])]

  async def list_models(self) -> list[dict[str, Any]]:
    if self.db is None:
      raise RuntimeError("rpcdispatch module requires db module")
    result = await self.db.run(list_models_request())
    return [dict(row) for row in (result.rows or [])]

  async def list_model_fields(self) -> list[dict[str, Any]]:
    if self.db is None:
      raise RuntimeError("rpcdispatch module requires db module")
    result = await self.db.run(list_model_fields_request())
    return [dict(row) for row in (result.rows or [])]

  async def list_tables(self) -> list[dict[str, Any]]:
    if self.db is None:
      raise RuntimeError("rpcdispatch module requires db module")
    response = await self.db.run(list_tables_request())
    return self._extract_payload(response) or []

  async def describe_table(self, table_name: str, table_schema: str) -> dict[str, Any]:
    if self.db is None:
      raise RuntimeError("rpcdispatch module requires db module")
    params = TableParams(table_schema=table_schema, name=table_name)
    columns = await self.db.run(list_columns_request(params))
    indexes = await self.db.run(list_indexes_request(params))
    foreign_keys = await self.db.run(list_foreign_keys_request(params))
    return {
      "columns": self._extract_payload(columns) or [],
      "indexes": self._extract_payload(indexes) or [],
      "foreign_keys": self._extract_payload(foreign_keys) or [],
    }

  async def list_views(self) -> list[dict[str, Any]]:
    if self.db is None:
      raise RuntimeError("rpcdispatch module requires db module")
    response = await self.db.run(list_views_request())
    return self._extract_payload(response) or []

  async def get_full_schema(self) -> Any:
    if self.db is None:
      raise RuntimeError("rpcdispatch module requires db module")
    response = await self.db.run(get_full_schema_request())
    return self._extract_payload(response)

  async def get_schema_version(self) -> Any:
    if self.db is None:
      raise RuntimeError("rpcdispatch module requires db module")
    response = await self.db.run(get_version_request())
    data = self._extract_payload(response) or {}
    if isinstance(data, dict):
      return data.get("element_value", data)
    return data

  async def dump_table(self, table_name: str, table_schema: str, max_rows: int) -> dict[str, Any]:
    if self.db is None:
      raise RuntimeError("rpcdispatch module requires db module")
    params = DumpTableParams(table_schema=table_schema, name=table_name)
    response = await self.db.run(dump_table_request(params))
    rows = self._extract_payload(response) or []
    if not isinstance(rows, list):
      rows = [rows]
    total_rows = len(rows)
    bounded_rows = rows[:max_rows]
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
    if self.db is None:
      raise RuntimeError("rpcdispatch module requires db module")
    params = QueryInfoSchemaParams(
      view_name=view_name,
      filter_column=filter_column,
      filter_value=filter_value,
    )
    response = await self.db.run(query_info_schema_request(params))
    return self._extract_payload(response) or []

  async def list_rpc_endpoints(self) -> list[str]:
    from rpc import HANDLERS

    return sorted(HANDLERS.keys())
