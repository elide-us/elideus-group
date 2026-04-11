"""MCP server bridge mounted into the FastAPI application."""

from __future__ import annotations

import contextvars
import logging
from os import getenv
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException
from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ToolAnnotations
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import Receive, Scope, Send

if TYPE_CHECKING:
  from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

_MCP_TOKEN = getenv("MCP_AGENT_TOKEN", "")
_hostname = "localhost"
_gateway_resolver: Callable[[], Any] | None = None
_AUTH_CONTEXT: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar("mcp_auth", default=None)

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


def _auth_challenge_headers() -> dict[str, str]:
  return {
    "WWW-Authenticate": f'Bearer resource_metadata="https://{_hostname}/.well-known/oauth-protected-resource"'
  }


async def mcp_auth_check(scope: Scope, receive: Receive, send: Send) -> dict[str, Any] | None:
  """Validate MCP auth from bearer token or JWT; send 401 when invalid."""
  if not _MCP_TOKEN:
    response = JSONResponse({"error": "MCP not configured"}, status_code=503)
    await response(scope, receive, send)
    return None

  request = Request(scope, receive)
  auth = request.headers.get("authorization", "")
  if not auth.startswith("Bearer "):
    response = JSONResponse(
      {"error": "Unauthorized"},
      status_code=401,
      headers=_auth_challenge_headers(),
    )
    await response(scope, receive, send)
    return None

  token = auth[7:]
  if token == _MCP_TOKEN:
    return {
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

  try:
    gateway = _get_gateway()
    claims = await gateway.validate_access_token(token)
    logging.info("[MCP Auth] JWT validated: sub=%s client_id=%s scopes=%s", claims.get("sub"), claims.get("client_id"), claims.get("scopes"))
    return {
      "type": "oauth",
      "scopes": set(str(claims.get("scopes", "")).split()),
      "user_guid": claims.get("sub"),
      "client_id": claims.get("client_id"),
    }
  except Exception as exc:
    logging.error("[MCP Auth] JWT validation failed: %s", exc, exc_info=True)
    response = JSONResponse(
      {"error": "Unauthorized"},
      status_code=401,
      headers=_auth_challenge_headers(),
    )
    await response(scope, receive, send)
    return None


async def mcp_asgi_handler(scope: Scope, receive: Receive, send: Send) -> None:
  """Authenticate and delegate to the MCP session manager ASGI handler."""
  if session_manager is None:
    response = JSONResponse({"error": "MCP not configured"}, status_code=503)
    await response(scope, receive, send)
    return

  auth = await mcp_auth_check(scope, receive, send)
  if auth is None:
    return

  token_handle = _AUTH_CONTEXT.set(auth)
  try:
    await session_manager.handle_request(scope, receive, send)
  finally:
    _AUTH_CONTEXT.reset(token_handle)


def init_session_manager() -> None:
  """Create the MCP session manager when MCP is configured."""
  global session_manager
  if not _MCP_TOKEN:
    logging.info("[MCP] skipped (MCP_AGENT_TOKEN not set)")
    return

  from mcp.server.streamable_http_manager import StreamableHTTPSessionManager as _Manager

  session_manager = _Manager(
    app=mcp._mcp_server,
    json_response=True,
    stateless=True,
  )
  logging.info("[MCP] session manager built, waiting for lifespan init")


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


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_list_tables(ctx: Context) -> Any:
  """List tables exposed by the reflection schema registry."""
  _check_scope(ctx, "mcp:schema:read")
  module = _get_gateway().app.state.rpcdispatch
  await module.on_ready()
  return await module.list_tables()


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_describe_table(ctx: Context, table_name: str, table_schema: str = "dbo") -> Any:
  """Describe a table by returning columns, indexes, and foreign keys."""
  _check_scope(ctx, "mcp:schema:read")
  module = _get_gateway().app.state.rpcdispatch
  await module.on_ready()
  return await module.describe_table(table_name, table_schema)


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_list_views(ctx: Context) -> Any:
  """List database views from reflection schema metadata."""
  _check_scope(ctx, "mcp:schema:read")
  module = _get_gateway().app.state.rpcdispatch
  await module.on_ready()
  return await module.list_views()


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_get_full_schema(ctx: Context) -> Any:
  """Return the full reflection schema snapshot payload."""
  _check_scope(ctx, "mcp:schema:read")
  module = _get_gateway().app.state.rpcdispatch
  await module.on_ready()
  return await module.get_full_schema()


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_get_schema_version(ctx: Context) -> Any:
  """Return the current schema version from reflection data metadata."""
  _check_scope(ctx, "mcp:schema:read")
  module = _get_gateway().app.state.rpcdispatch
  await module.on_ready()
  return {"version": await module.get_schema_version()}


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_dump_table(ctx: Context, table_name: str, table_schema: str = "dbo", max_rows: int = 100) -> Any:
  """Dump table rows from reflection data and return a bounded result set."""
  _check_scope(ctx, "mcp:data:read")
  module = _get_gateway().app.state.rpcdispatch
  await module.on_ready()
  return await module.dump_table(table_name, table_schema, max_rows)


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_query_info_schema(ctx: Context, view_name: str, filter_column: str | None = None, filter_value: str | None = None) -> Any:
  """Query whitelisted INFORMATION_SCHEMA views with optional equality filter."""
  _check_scope(ctx, "mcp:schema:read")
  module = _get_gateway().app.state.rpcdispatch
  await module.on_ready()
  return await module.query_info_schema(view_name, filter_column, filter_value)


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_list_domains(ctx: Context) -> Any:
  """Enumerate query registry domains, subdomains, and operation versions."""
  _check_scope(ctx, "mcp:rpc:list")
  module = _get_gateway().app.state.rpcdispatch
  await module.on_ready()
  return {"domains": await module.list_domains()}


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_list_rpc_endpoints(ctx: Context) -> Any:
  """List available top-level RPC domains."""
  _check_scope(ctx, "mcp:rpc:list")
  module = _get_gateway().app.state.rpcdispatch
  await module.on_ready()
  return {"endpoints": await module.list_rpc_endpoints()}


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_list_rpc_domains(ctx: Context) -> Any:
  """List RPC domain registrations from the reflection dispatch catalog."""
  _check_scope(ctx, "mcp:rpc:list")
  module = _get_gateway().app.state.rpcdispatch
  await module.on_ready()
  return await module.list_domains()


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_list_rpc_subdomains(ctx: Context) -> Any:
  """List RPC subdomain registrations from the reflection dispatch catalog."""
  _check_scope(ctx, "mcp:rpc:list")
  module = _get_gateway().app.state.rpcdispatch
  await module.on_ready()
  return await module.list_subdomains()


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_list_rpc_functions(ctx: Context) -> Any:
  """List RPC function registrations with module bindings and model references."""
  _check_scope(ctx, "mcp:rpc:list")
  module = _get_gateway().app.state.rpcdispatch
  await module.on_ready()
  return await module.list_functions()


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_list_rpc_models(ctx: Context) -> Any:
  """List RPC Pydantic model registrations with domain and version metadata."""
  _check_scope(ctx, "mcp:rpc:list")
  module = _get_gateway().app.state.rpcdispatch
  await module.on_ready()
  return await module.list_models()


@mcp.tool(annotations=_TOOL_ANNOTATIONS)
async def oracle_list_rpc_model_fields(ctx: Context) -> Any:
  """List RPC model field registrations with EDT types, nullability, and references."""
  _check_scope(ctx, "mcp:rpc:list")
  module = _get_gateway().app.state.rpcdispatch
  await module.on_ready()
  return await module.list_model_fields()
