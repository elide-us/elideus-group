"""MCP server bridge mounted into the FastAPI application."""

from __future__ import annotations

import contextvars
import importlib
import logging
import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException
from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ToolAnnotations
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Mount

from queryregistry.finance.credits import set_credits_request
from queryregistry.finance.credits.models import SetCreditsParams
from queryregistry.handler import HANDLERS as QR_HANDLERS
from queryregistry.handler import dispatch_query_request
from queryregistry.models import DBRequest
from queryregistry.providers.mssql import run_json_many
from rpc import HANDLERS as RPC_HANDLERS

if TYPE_CHECKING:
  from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

_MCP_TOKEN = os.environ.get("MCP_AGENT_TOKEN", "")
_hostname = os.environ.get("MCP_HOSTNAME", "localhost")
_gateway_resolver: Callable[[], Any] | None = None
_AUTH_CONTEXT: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar("mcp_auth", default=None)
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
session_manager: StreamableHTTPSessionManager | None = None
_TOOL_ANNOTATIONS = ToolAnnotations(
  readOnlyHint=True,
  destructiveHint=False,
  idempotentHint=True,
  openWorldHint=False,
)


def set_gateway_resolver(resolver: Callable[[], Any] | None) -> None:
  global _gateway_resolver
  _gateway_resolver = resolver


def _get_gateway() -> Any:
  if _gateway_resolver is None:
    raise RuntimeError("MCP gateway resolver is not configured")
  gateway = _gateway_resolver()
  if gateway is None:
    raise RuntimeError("MCP gateway is unavailable")
  global _hostname
  hostname = getattr(gateway, "hostname", None)
  if hostname:
    _hostname = str(hostname)
  return gateway


class MCPAuthMiddleware(BaseHTTPMiddleware):
  """Bearer-token gate: static token OR MCP OAuth JWT."""

  async def dispatch(self, request: Any, call_next: Any) -> JSONResponse | Any:
    if not _MCP_TOKEN:
      return JSONResponse({"error": "MCP not configured"}, status_code=503)

    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
      return JSONResponse(
        {"error": "Unauthorized"},
        status_code=401,
        headers={
          "WWW-Authenticate": f'Bearer resource_metadata="https://{_hostname}/.well-known/oauth-protected-resource"'
        },
      )

    token = auth[7:]

    if token == _MCP_TOKEN:
      request.state.mcp_auth = {
        "type": "static",
        "scopes": {
          "mcp:schema:read",
          "mcp:data:read",
          "mcp:rpc:list",
          "mcp:schema:write",
          "mcp:data:write",
          "mcp:rpc:execute",
          "mcp:admin",
        },
        "user_guid": None,
        "client_id": None,
      }
      token_handle = _AUTH_CONTEXT.set(request.state.mcp_auth)
      try:
        return await call_next(request)
      finally:
        _AUTH_CONTEXT.reset(token_handle)

    try:
      gateway = _get_gateway()
      claims = await gateway.validate_access_token(token)
      request.state.mcp_auth = {
        "type": "oauth",
        "scopes": set(str(claims.get("scopes", "")).split()),
        "user_guid": claims.get("sub"),
        "client_id": claims.get("client_id"),
      }
      token_handle = _AUTH_CONTEXT.set(request.state.mcp_auth)
      try:
        return await call_next(request)
      finally:
        _AUTH_CONTEXT.reset(token_handle)
    except Exception:
      return JSONResponse(
        {"error": "Unauthorized"},
        status_code=401,
        headers={
          "WWW-Authenticate": f'Bearer resource_metadata="https://{_hostname}/.well-known/oauth-protected-resource"'
        },
      )


def _check_scope(ctx: Context, required_scope: str) -> dict[str, Any]:
  """Check scope authorization from middleware-injected auth state."""
  mcp_auth = None
  request_context = getattr(ctx, "request_context", None)
  request = getattr(request_context, "request", None) if request_context else None
  if request is not None:
    mcp_auth = getattr(request.state, "mcp_auth", None)
  if mcp_auth is None:
    mcp_auth = _AUTH_CONTEXT.get()
  if mcp_auth is None:
    raise HTTPException(status_code=401, detail="Not authenticated")
  if required_scope not in mcp_auth["scopes"]:
    raise HTTPException(status_code=403, detail=f"Scope '{required_scope}' required")
  return mcp_auth


async def _consume_credit(auth: dict[str, Any], *, cost: int) -> None:
  if cost <= 0 or auth.get("type") != "oauth":
    return
  gateway = _get_gateway()
  client_id = auth.get("client_id")
  if not client_id:
    raise HTTPException(status_code=401, detail="OAuth client binding is missing")
  client = await gateway.get_client(str(client_id))
  if not client:
    raise HTTPException(status_code=401, detail="OAuth client is invalid")
  user_guid, credits = await gateway.resolve_agent_credits(int(client["recid"]))
  if credits < cost:
    raise HTTPException(status_code=402, detail="Insufficient credits")
  await gateway.db.run(set_credits_request(SetCreditsParams(guid=user_guid, credits=credits - cost)))


def _quote_ident(identifier: str) -> str:
  return "[" + identifier.replace("]", "]]" ) + "]"


def _extract_payload(response: Any) -> Any:
  if hasattr(response, "payload"):
    return response.payload
  return response


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_list_tables(ctx: Context) -> Any:
  """List tables exposed by the reflection schema registry."""
  _check_scope(ctx, "mcp:schema:read")
  response = await dispatch_query_request(DBRequest(op="db:reflection:schema:list_tables:1", payload={}))
  return _extract_payload(response)


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_describe_table(
  ctx: Context,
  table_name: str,
  table_schema: str = "dbo",
) -> dict[str, Any]:
  """Describe a table by returning columns, indexes, and foreign keys."""
  _check_scope(ctx, "mcp:schema:read")
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
  _check_scope(ctx, "mcp:schema:read")
  response = await dispatch_query_request(DBRequest(op="db:reflection:schema:list_views:1", payload={}))
  return _extract_payload(response)


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_get_full_schema(ctx: Context) -> Any:
  """Return the full reflection schema snapshot payload."""
  _check_scope(ctx, "mcp:schema:read")
  response = await dispatch_query_request(DBRequest(op="db:reflection:schema:get_full_schema:1", payload={}))
  return _extract_payload(response)


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_get_schema_version(ctx: Context) -> Any:
  """Return the current schema version from reflection data metadata."""
  _check_scope(ctx, "mcp:data:read")
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
  auth = _check_scope(ctx, "mcp:data:read")
  await _consume_credit(auth, cost=1)
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
  auth = _check_scope(ctx, "mcp:data:read")
  await _consume_credit(auth, cost=1)
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
  _check_scope(ctx, "mcp:rpc:list")
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
  _check_scope(ctx, "mcp:rpc:list")
  return sorted(RPC_HANDLERS.keys())


def get_mcp_app() -> Starlette | None:
  """Return the MCP ASGI app wrapped with auth middleware, or None if unconfigured."""
  global session_manager
  if not _MCP_TOKEN:
    logging.info("[MCP] skipped (MCP_AGENT_TOKEN not set)")
    return None

  from mcp.server.streamable_http_manager import StreamableHTTPSessionManager as _Manager

  session_manager = _Manager(
    app=mcp._mcp_server,
    json_response=True,
    stateless=True,
  )

  mcp_inner = Starlette(
    routes=[
      Mount("/mcp", app=session_manager.handle_request),
    ],
  )

  app = Starlette(middleware=[Middleware(MCPAuthMiddleware)])
  app.mount("/", mcp_inner)
  logging.info("[MCP] app built, waiting for lifespan init")
  return app
