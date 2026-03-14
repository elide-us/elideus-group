"""MCP server bridge mounted into the FastAPI application."""

from __future__ import annotations

import importlib
import logging
import os
from typing import Any

from fastapi import HTTPException
from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ToolAnnotations
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Mount

from queryregistry.handler import HANDLERS as QR_HANDLERS
from queryregistry.handler import dispatch_query_request
from queryregistry.models import DBRequest
from queryregistry.providers.mssql import run_json_many
from rpc import HANDLERS as RPC_HANDLERS

_MCP_TOKEN = os.environ.get("MCP_AGENT_TOKEN", "")
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

mcp = FastMCP("oracle_rpc_mcp")
_TOOL_ANNOTATIONS = ToolAnnotations(
  readOnlyHint=True,
  destructiveHint=False,
  idempotentHint=True,
  openWorldHint=False,
)


class MCPAuthMiddleware(BaseHTTPMiddleware):
  """Simple bearer-token gate for the mounted MCP app."""

  async def dispatch(self, request: Any, call_next: Any) -> JSONResponse | Any:
    if not _MCP_TOKEN:
      return JSONResponse({"error": "MCP not configured"}, status_code=503)
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer ") or auth[7:] != _MCP_TOKEN:
      return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return await call_next(request)


def _quote_ident(identifier: str) -> str:
  return "[" + identifier.replace("]", "]]" ) + "]"


def _extract_payload(response: Any) -> Any:
  if hasattr(response, "payload"):
    return response.payload
  return response



@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_list_tables(ctx: Context) -> Any:
  """List tables exposed by the reflection schema registry."""
  response = await dispatch_query_request(DBRequest(op="db:reflection:schema:list_tables:1", payload={}))
  return _extract_payload(response)


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_describe_table(
  ctx: Context,
  table_name: str,
  table_schema: str = "dbo",
) -> dict[str, Any]:
  """Describe a table by returning columns, indexes, and foreign keys."""
  payload = {"table_schema": table_schema, "name": table_name}
  columns = await dispatch_query_request(DBRequest(op="db:reflection:schema:list_columns:1", payload=payload))
  indexes = await dispatch_query_request(DBRequest(op="db:reflection:schema:list_indexes:1", payload=payload))
  foreign_keys = await dispatch_query_request(DBRequest(op="db:reflection:schema:list_foreign_keys:1", payload=payload))
  return {
    "columns": _extract_payload(columns),
    "indexes": _extract_payload(indexes),
    "foreign_keys": _extract_payload(foreign_keys),
  }


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_list_views(ctx: Context) -> Any:
  """List database views from reflection schema metadata."""
  response = await dispatch_query_request(DBRequest(op="db:reflection:schema:list_views:1", payload={}))
  return _extract_payload(response)


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_get_full_schema(ctx: Context) -> Any:
  """Return the full reflection schema snapshot payload."""
  response = await dispatch_query_request(DBRequest(op="db:reflection:schema:get_full_schema:1", payload={}))
  return _extract_payload(response)


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_get_schema_version(ctx: Context) -> Any:
  """Return the current schema version from reflection data metadata."""
  response = await dispatch_query_request(DBRequest(op="db:reflection:data:get_version:1", payload={}))
  return _extract_payload(response)


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_dump_table(
  ctx: Context,
  table_name: str,
  table_schema: str = "dbo",
  max_rows: int = 100,
) -> dict[str, Any]:
  """Dump table rows from reflection data and return a bounded result set."""
  bounded_max_rows = max(0, min(max_rows, 1000))
  response = await dispatch_query_request(
    DBRequest(op="db:reflection:data:dump_table:1", payload={"table_schema": table_schema, "name": table_name})
  )
  rows = _extract_payload(response) or []
  if not isinstance(rows, list):
    rows = [rows]
  total_rows = len(rows)
  return {
    "rows": rows[:bounded_max_rows],
    "truncated": total_rows > bounded_max_rows,
    "total_rows": total_rows,
  }


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_query_info_schema(
  ctx: Context,
  view_name: str,
  filter_column: str | None = None,
  filter_value: str | None = None,
) -> Any:
  """Query whitelisted INFORMATION_SCHEMA views with optional equality filter."""
  if view_name not in _ALLOWED_VIEWS:
    raise HTTPException(status_code=400, detail=f"Unsupported INFORMATION_SCHEMA view: {view_name}")

  sql = f"SELECT * FROM INFORMATION_SCHEMA.{_quote_ident(view_name)}"
  params: tuple[str, ...] = ()
  if filter_column is not None and filter_value is not None:
    sql += f" WHERE {_quote_ident(filter_column)} = ?"
    params = (filter_value,)
  sql += " FOR JSON PATH;"
  return await run_json_many(sql, params)


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_list_domains(ctx: Context) -> dict[str, Any]:
  """Enumerate query registry domains, subdomains, and operation versions."""
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
  return results


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_list_rpc_endpoints(ctx: Context) -> list[str]:
  """List available top-level RPC domains."""
  return sorted(RPC_HANDLERS.keys())


def get_mcp_app() -> Starlette | None:
  """Return the MCP ASGI app wrapped with auth middleware, or None if unconfigured."""
  if not _MCP_TOKEN:
    logging.info("[MCP] skipped (MCP_AGENT_TOKEN not set)")
    return None

  from contextlib import asynccontextmanager
  from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

  session_manager = StreamableHTTPSessionManager(
    app=mcp._mcp_server,
    json_response=True,
    stateless=True,
  )

  @asynccontextmanager
  async def mcp_lifespan(app: Any):
    async with session_manager.run():
      logging.info("[MCP] server mounted at /mcp")
      yield

  mcp_inner = Starlette(
    lifespan=mcp_lifespan,
    routes=[
      Mount("/mcp", app=session_manager.handle_request),
    ],
  )

  app = Starlette(middleware=[Middleware(MCPAuthMiddleware)])
  app.mount("/", mcp_inner)
  return app
