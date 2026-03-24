"""Identity MCP agents query registry helpers."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
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
  "create_agent_token_request",
  "create_auth_code_request",
  "consume_auth_code_request",
  "get_agent_by_client_id_request",
  "get_agent_token_request",
  "link_agent_user_request",
  "list_user_agents_request",
  "register_agent_request",
  "revoke_agent_request",
  "revoke_agent_token_request",
]


def _request(name: str, payload: dict[str, object]) -> DBRequest:
  return DBRequest(op=f"db:identity:mcp_agents:{name}:1", payload=payload)


def register_agent_request(params: RegisterAgentParams) -> DBRequest:
  return _request("register", params.model_dump(exclude_none=True))


def get_agent_by_client_id_request(params: ClientIdParams) -> DBRequest:
  return _request("get_by_client_id", params.model_dump())


def link_agent_user_request(params: LinkAgentUserParams) -> DBRequest:
  return _request("link_user", params.model_dump())


def revoke_agent_request(params: ClientIdParams) -> DBRequest:
  return _request("revoke", params.model_dump())


def list_user_agents_request(params: UserGuidParams) -> DBRequest:
  return _request("list_by_user", params.model_dump())


def create_auth_code_request(params: CreateAuthCodeParams) -> DBRequest:
  return _request("create_auth_code", params.model_dump())


def consume_auth_code_request(params: ConsumeAuthCodeParams) -> DBRequest:
  return _request("consume_auth_code", params.model_dump())


def create_agent_token_request(params: CreateAgentTokenParams) -> DBRequest:
  return _request("create_token", params.model_dump(exclude_none=True))


def get_agent_token_request(params: RefreshTokenParams) -> DBRequest:
  return _request("get_token", params.model_dump())


def revoke_agent_token_request(params: RevokeTokenParams) -> DBRequest:
  return _request("revoke_token", params.model_dump())
