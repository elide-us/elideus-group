"""Identity MCP agents query registry service models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

__all__ = [
  "AgentRecidParams",
  "ClientIdParams",
  "CreateAgentTokenParams",
  "CreateAuthCodeParams",
  "ConsumeAuthCodeParams",
  "LinkAgentUserParams",
  "RefreshTokenParams",
  "RegisterAgentParams",
  "RevokeTokenParams",
  "UserGuidParams",
]


class RegisterAgentParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  client_name: str
  redirect_uris: str | None = None
  grant_types: str = "authorization_code"
  response_types: str = "code"
  scopes: str = "mcp:schema:read mcp:data:read mcp:rpc:list"
  ip_address: str | None = None
  user_agent: str | None = None


class AgentRecidParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  agents_recid: int


class ClientIdParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  client_id: str


class LinkAgentUserParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  client_id: str
  users_guid: str


class UserGuidParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  users_guid: str


class CreateAuthCodeParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  agents_recid: int
  users_guid: str
  code: str
  code_challenge: str
  code_method: str = "S256"
  redirect_uri: str
  scopes: str
  expires_on: datetime


class ConsumeAuthCodeParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  code: str


class CreateAgentTokenParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  agents_recid: int
  access_token: str
  refresh_token: str | None = None
  access_exp: datetime
  refresh_exp: datetime | None = None
  scopes: str


class RefreshTokenParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  refresh_token: str


class RevokeTokenParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  agents_recid: int
