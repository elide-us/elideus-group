"""System domain handler implementations."""

from __future__ import annotations

from typing import Sequence

from fastapi import HTTPException

from queryregistry.models import DBRequest, DBResponse

from .config.handler import handle_config_request
from .conversations.handler import handle_conversations_request
from .personas.handler import handle_personas_request
from .public.handler import handle_public_request
from .renewals.handler import handle_renewals_request
from .roles.handler import handle_roles_request
from .scheduled_tasks.handler import handle_scheduled_tasks_request
from .workflows.handler import handle_workflows_request

__all__ = ["handle_system_request"]

HANDLERS = {
  "config": handle_config_request,
  "conversations": handle_conversations_request,
  "personas": handle_personas_request,
  "public": handle_public_request,
  "renewals": handle_renewals_request,
  "roles": handle_roles_request,
  "scheduled_tasks": handle_scheduled_tasks_request,
  "workflows": handle_workflows_request,
}


async def handle_system_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  if not path:
    raise HTTPException(status_code=404, detail="Unknown system registry operation")
  subdomain = path[0]
  handler = HANDLERS.get(subdomain)
  if handler is None:
    raise HTTPException(status_code=404, detail="Unknown system registry operation")
  return await handler(path[1:], request, provider=provider)
