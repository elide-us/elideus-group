"""Identity MCP agents query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  AgentRecidParams,
  ClientIdParams,
  CreateAgentTokenParams,
  CreateAuthCodeParams,
  ConsumeAuthCodeParams,
  LinkAgentUserParams,
  RefreshTokenParams,
  RegisterAgentParams,
  RevokeTokenParams,
  UserGuidParams,
)

__all__ = [
  "consume_auth_code_v1",
  "create_auth_code_v1",
  "create_token_v1",
  "get_by_client_id_v1",
  "get_by_recid_v1",
  "get_token_v1",
  "link_user_v1",
  "list_by_user_v1",
  "register_v1",
  "revoke_token_v1",
  "revoke_v1",
]

AgentOperationCallable = Callable[[dict[str, Any]], Awaitable[DBResponse]]

_REGISTER_DISPATCHERS: dict[str, AgentOperationCallable] = {"mssql": mssql.register_v1}
_GET_BY_CLIENT_ID_DISPATCHERS: dict[str, AgentOperationCallable] = {
  "mssql": mssql.get_by_client_id_v1,
}
_GET_BY_RECID_DISPATCHERS: dict[str, AgentOperationCallable] = {
  "mssql": mssql.get_by_recid_v1,
}
_LINK_USER_DISPATCHERS: dict[str, AgentOperationCallable] = {"mssql": mssql.link_user_v1}
_REVOKE_DISPATCHERS: dict[str, AgentOperationCallable] = {"mssql": mssql.revoke_v1}
_LIST_BY_USER_DISPATCHERS: dict[str, AgentOperationCallable] = {
  "mssql": mssql.list_by_user_v1,
}
_CREATE_AUTH_CODE_DISPATCHERS: dict[str, AgentOperationCallable] = {
  "mssql": mssql.create_auth_code_v1,
}
_CONSUME_AUTH_CODE_DISPATCHERS: dict[str, AgentOperationCallable] = {
  "mssql": mssql.consume_auth_code_v1,
}
_CREATE_TOKEN_DISPATCHERS: dict[str, AgentOperationCallable] = {"mssql": mssql.create_token_v1}
_GET_TOKEN_DISPATCHERS: dict[str, AgentOperationCallable] = {"mssql": mssql.get_token_v1}
_REVOKE_TOKEN_DISPATCHERS: dict[str, AgentOperationCallable] = {
  "mssql": mssql.revoke_token_v1,
}


def _resolve_dispatcher(
  dispatchers: dict[str, AgentOperationCallable],
  *,
  provider: str,
) -> AgentOperationCallable:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity mcp_agents registry")
  return dispatcher


async def register_v1(request: DBRequest, *, provider: str) -> DBResponse:
  dispatcher = _resolve_dispatcher(_REGISTER_DISPATCHERS, provider=provider)
  params = RegisterAgentParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump(exclude_none=True))
  return DBResponse(op=request.op, payload=result.payload, rows=result.rows, rowcount=result.rowcount)




async def get_by_recid_v1(request: DBRequest, *, provider: str) -> DBResponse:
  dispatcher = _resolve_dispatcher(_GET_BY_RECID_DISPATCHERS, provider=provider)
  params = AgentRecidParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rows=result.rows, rowcount=result.rowcount)


async def get_by_client_id_v1(request: DBRequest, *, provider: str) -> DBResponse:
  dispatcher = _resolve_dispatcher(_GET_BY_CLIENT_ID_DISPATCHERS, provider=provider)
  params = ClientIdParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rows=result.rows, rowcount=result.rowcount)


async def link_user_v1(request: DBRequest, *, provider: str) -> DBResponse:
  dispatcher = _resolve_dispatcher(_LINK_USER_DISPATCHERS, provider=provider)
  params = LinkAgentUserParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def revoke_v1(request: DBRequest, *, provider: str) -> DBResponse:
  dispatcher = _resolve_dispatcher(_REVOKE_DISPATCHERS, provider=provider)
  params = ClientIdParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_by_user_v1(request: DBRequest, *, provider: str) -> DBResponse:
  dispatcher = _resolve_dispatcher(_LIST_BY_USER_DISPATCHERS, provider=provider)
  params = UserGuidParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rows=result.rows, rowcount=result.rowcount)


async def create_auth_code_v1(request: DBRequest, *, provider: str) -> DBResponse:
  dispatcher = _resolve_dispatcher(_CREATE_AUTH_CODE_DISPATCHERS, provider=provider)
  params = CreateAuthCodeParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rows=result.rows, rowcount=result.rowcount)


async def consume_auth_code_v1(request: DBRequest, *, provider: str) -> DBResponse:
  dispatcher = _resolve_dispatcher(_CONSUME_AUTH_CODE_DISPATCHERS, provider=provider)
  params = ConsumeAuthCodeParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rows=result.rows, rowcount=result.rowcount)


async def create_token_v1(request: DBRequest, *, provider: str) -> DBResponse:
  dispatcher = _resolve_dispatcher(_CREATE_TOKEN_DISPATCHERS, provider=provider)
  params = CreateAgentTokenParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump(exclude_none=True))
  return DBResponse(op=request.op, payload=result.payload, rows=result.rows, rowcount=result.rowcount)


async def get_token_v1(request: DBRequest, *, provider: str) -> DBResponse:
  dispatcher = _resolve_dispatcher(_GET_TOKEN_DISPATCHERS, provider=provider)
  params = RefreshTokenParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rows=result.rows, rowcount=result.rowcount)


async def revoke_token_v1(request: DBRequest, *, provider: str) -> DBResponse:
  dispatcher = _resolve_dispatcher(_REVOKE_TOKEN_DISPATCHERS, provider=provider)
  params = RevokeTokenParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
