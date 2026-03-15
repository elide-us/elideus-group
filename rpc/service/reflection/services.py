"""Service functions for service.reflection RPC operations."""

from __future__ import annotations

import importlib
from typing import Any

from fastapi import HTTPException, Request

from queryregistry.handler import HANDLERS as QR_HANDLERS
from queryregistry.models import DBRequest
from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.db_module import DbModule

from .models import (
  DescribeTableRequest1,
  DescribeTableResponse1,
  DomainsResponse1,
  DumpTableRequest1,
  DumpTableResponse1,
  QueryInfoSchemaRequest1,
  RpcEndpointsResponse1,
  SchemaVersionResponse1,
  TableListResponse1,
)

_ALLOWED_VIEWS = frozenset({
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


def _extract_payload(response: Any) -> Any:
  if hasattr(response, "payload"):
    return response.payload
  return response


async def service_reflection_list_tables_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  db: DbModule = request.app.state.db
  await db.on_ready()
  response = await db.run(DBRequest(op="db:reflection:schema:list_tables:1", payload={}))
  payload = TableListResponse1(tables=_extract_payload(response) or [])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_reflection_describe_table_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  data = DescribeTableRequest1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  qr_payload = {"table_schema": data.table_schema, "name": data.table_name}
  columns = await db.run(DBRequest(op="db:reflection:schema:list_columns:1", payload=qr_payload))
  indexes = await db.run(DBRequest(op="db:reflection:schema:list_indexes:1", payload=qr_payload))
  foreign_keys = await db.run(DBRequest(op="db:reflection:schema:list_foreign_keys:1", payload=qr_payload))
  payload = DescribeTableResponse1(
    columns=_extract_payload(columns) or [],
    indexes=_extract_payload(indexes) or [],
    foreign_keys=_extract_payload(foreign_keys) or [],
  )
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_reflection_list_views_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  db: DbModule = request.app.state.db
  await db.on_ready()
  response = await db.run(DBRequest(op="db:reflection:schema:list_views:1", payload={}))
  payload = TableListResponse1(tables=_extract_payload(response) or [])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_reflection_get_full_schema_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  db: DbModule = request.app.state.db
  await db.on_ready()
  response = await db.run(DBRequest(op="db:reflection:schema:get_full_schema:1", payload={}))
  return RPCResponse(op=rpc_request.op, payload=_extract_payload(response), version=rpc_request.version)


async def service_reflection_get_schema_version_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  db: DbModule = request.app.state.db
  await db.on_ready()
  response = await db.run(DBRequest(op="db:reflection:data:get_version:1", payload={}))
  data = _extract_payload(response) or {}
  payload = SchemaVersionResponse1(version=data.get("element_value", data))
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_reflection_dump_table_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  data = DumpTableRequest1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  response = await db.run(
    DBRequest(op="db:reflection:data:dump_table:1", payload={"table_schema": data.table_schema, "name": data.table_name})
  )
  rows = _extract_payload(response) or []
  if not isinstance(rows, list):
    rows = [rows]
  total_rows = len(rows)
  bounded = rows[:data.max_rows]
  payload = DumpTableResponse1(rows=bounded, truncated=total_rows > data.max_rows, total_rows=total_rows)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_reflection_query_info_schema_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  data = QueryInfoSchemaRequest1(**(rpc_request.payload or {}))
  if data.view_name not in _ALLOWED_VIEWS:
    raise HTTPException(status_code=400, detail=f"Unsupported INFORMATION_SCHEMA view: {data.view_name}")
  db: DbModule = request.app.state.db
  await db.on_ready()
  qr_payload: dict[str, Any] = {"view_name": data.view_name}
  if data.filter_column is not None and data.filter_value is not None:
    qr_payload["filter_column"] = data.filter_column
    qr_payload["filter_value"] = data.filter_value
  response = await db.run(DBRequest(op="db:reflection:data:query_info_schema:1", payload=qr_payload))
  rows = _extract_payload(response) or []
  return RPCResponse(op=rpc_request.op, payload=rows, version=rpc_request.version)


async def service_reflection_list_domains_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  results: dict[str, Any] = {}
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
      results[domain] = domain_entry
    except Exception as exc:
      results[domain] = {"error": str(exc)}
  payload = DomainsResponse1(domains=results)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_reflection_list_rpc_endpoints_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  from rpc import HANDLERS

  payload = RpcEndpointsResponse1(endpoints=sorted(HANDLERS.keys()))
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
