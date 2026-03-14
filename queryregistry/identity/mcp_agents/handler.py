"""Identity MCP agents handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  consume_auth_code_v1,
  create_auth_code_v1,
  create_token_v1,
  get_by_client_id_v1,
  get_by_recid_v1,
  get_token_v1,
  link_user_v1,
  list_by_user_v1,
  register_v1,
  revoke_token_v1,
  revoke_v1,
)

__all__ = ["handle_mcp_agents_request"]

DISPATCHERS = {
  ("register", "1"): register_v1,
  ("get_by_client_id", "1"): get_by_client_id_v1,
  ("get_by_recid", "1"): get_by_recid_v1,
  ("link_user", "1"): link_user_v1,
  ("revoke", "1"): revoke_v1,
  ("list_by_user", "1"): list_by_user_v1,
  ("create_auth_code", "1"): create_auth_code_v1,
  ("consume_auth_code", "1"): consume_auth_code_v1,
  ("create_token", "1"): create_token_v1,
  ("get_token", "1"): get_token_v1,
  ("revoke_token", "1"): revoke_token_v1,
}


async def handle_mcp_agents_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  return await dispatch_subdomain_request(
    path,
    request,
    provider=provider,
    dispatchers=DISPATCHERS,
    detail="Unknown identity mcp_agents operation",
  )
