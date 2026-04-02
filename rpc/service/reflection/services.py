"""Service functions for service.reflection RPC operations."""

from __future__ import annotations

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  DescribeTableRequest1,
  DescribeTableResponse1,
  DomainsResponse1,
  EdtMappingsResponse1,
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


async def service_reflection_list_tables_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  module = request.app.state.rpcdispatch
  await module.on_ready()
  rows = await module.list_tables()
  payload = TableListResponse1(tables=rows or [])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_reflection_describe_table_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  data = DescribeTableRequest1(**(rpc_request.payload or {}))
  module = request.app.state.rpcdispatch
  await module.on_ready()
  description = await module.describe_table(data.table_name, data.table_schema)
  payload = DescribeTableResponse1(
    columns=description.get("columns") or [],
    indexes=description.get("indexes") or [],
    foreign_keys=description.get("foreign_keys") or [],
  )
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_reflection_list_views_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  module = request.app.state.rpcdispatch
  await module.on_ready()
  rows = await module.list_views()
  payload = TableListResponse1(tables=rows or [])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_reflection_get_full_schema_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  module = request.app.state.rpcdispatch
  await module.on_ready()
  schema = await module.get_full_schema()
  return RPCResponse(op=rpc_request.op, payload=schema, version=rpc_request.version)


async def service_reflection_get_schema_version_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  module = request.app.state.rpcdispatch
  await module.on_ready()
  version = await module.get_schema_version()
  payload = SchemaVersionResponse1(version=version)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_reflection_dump_table_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  data = DumpTableRequest1(**(rpc_request.payload or {}))
  module = request.app.state.rpcdispatch
  await module.on_ready()
  dump = await module.dump_table(data.table_name, data.table_schema, data.max_rows)
  payload = DumpTableResponse1(
    rows=dump.get("rows") or [],
    truncated=bool(dump.get("truncated")),
    total_rows=int(dump.get("total_rows") or 0),
  )
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_reflection_query_info_schema_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  data = QueryInfoSchemaRequest1(**(rpc_request.payload or {}))
  if data.view_name not in _ALLOWED_VIEWS:
    raise HTTPException(status_code=400, detail=f"Unsupported INFORMATION_SCHEMA view: {data.view_name}")
  module = request.app.state.rpcdispatch
  await module.on_ready()
  rows = await module.query_info_schema(data.view_name, data.filter_column, data.filter_value)
  return RPCResponse(op=rpc_request.op, payload=rows, version=rpc_request.version)


async def service_reflection_list_domains_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  module = request.app.state.rpcdispatch
  await module.on_ready()
  domains = await module.list_domains()
  payload = DomainsResponse1(domains=domains)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_reflection_list_rpc_endpoints_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  module = request.app.state.rpcdispatch
  await module.on_ready()
  endpoints = await module.list_rpc_endpoints()
  payload = RpcEndpointsResponse1(endpoints=endpoints)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_reflection_list_edt_mappings_v1(request: Request) -> RPCResponse:
  rpc_request, _, _ = await unbox_request(request)
  module = request.app.state.rpcdispatch
  await module.on_ready()
  mappings = await module.list_edt_mappings()
  payload = EdtMappingsResponse1(mappings=mappings)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
