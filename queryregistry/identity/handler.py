"""Identity domain handler implementations."""

from __future__ import annotations

from typing import Sequence

from fastapi import HTTPException

from queryregistry.models import DBRequest, DBResponse

from .audit.handler import handle_audit_request
from .auth.handler import handle_auth_request
from .enablements.handler import handle_enablements_request
from .mcp_agents.handler import handle_mcp_agents_request
from .profiles.handler import handle_profiles_request
from .roles.handler import handle_roles_request
from .sessions.handler import handle_sessions_request
from .users.handler import handle_users_request

__all__ = ["handle_identity_request"]

HANDLERS = {
  "audit": handle_audit_request,
  "auth": handle_auth_request,
  "enablements": handle_enablements_request,
  "mcp_agents": handle_mcp_agents_request,
  "profiles": handle_profiles_request,
  "roles": handle_roles_request,
  "sessions": handle_sessions_request,
  "users": handle_users_request,
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
