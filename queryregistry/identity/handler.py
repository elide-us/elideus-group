"""Identity domain handler implementations."""

from __future__ import annotations

from typing import Sequence

from fastapi import HTTPException

from queryregistry.models import DBRequest, DBResponse

from .accounts.handler import handle_accounts_request
from .audit.handler import handle_audit_request
from .mcp_agents.handler import handle_mcp_agents_request
from .profiles.handler import handle_profiles_request
from .providers.handler import handle_providers_request
from .role_memberships.handler import handle_role_memberships_request
from .sessions.handler import handle_sessions_request

__all__ = ["handle_identity_request"]

HANDLERS = {
  "accounts": handle_accounts_request,
  "audit": handle_audit_request,
  "mcp_agents": handle_mcp_agents_request,
  "profiles": handle_profiles_request,
  "providers": handle_providers_request,
  "role_memberships": handle_role_memberships_request,
  "sessions": handle_sessions_request,
}


async def handle_identity_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  if not path:
    raise HTTPException(status_code=404, detail="Unknown identity registry operation")
  subdomain = path[0]
  handler = HANDLERS.get(subdomain)
  if handler is None:
    raise HTTPException(status_code=404, detail="Unknown identity registry operation")
  return await handler(path[1:], request, provider=provider)
