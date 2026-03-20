"""System domain handler implementations."""

from __future__ import annotations

from typing import Sequence

from fastapi import HTTPException

from queryregistry.models import DBRequest, DBResponse

from .async_tasks.handler import handle_async_tasks_request
from .batch_jobs.handler import handle_batch_jobs_request
from .config.handler import handle_config_request
from .conversations.handler import handle_conversations_request
from .configuration.handler import handle_configuration_request
from .integrations.handler import handle_integrations_request
from .links.handler import handle_links_request
from .models_registry.handler import handle_models_request
from .personas.handler import handle_personas_request
from .public_vars.handler import handle_public_vars_request
from .renewals.handler import handle_renewals_request
from .roles.handler import handle_roles_request
from .routes.handler import handle_routes_request
from .service_pages.handler import handle_service_pages_request

__all__ = ["handle_system_request"]

HANDLERS = {
  "async_tasks": handle_async_tasks_request,
  "batch_jobs": handle_batch_jobs_request,
  "configuration": handle_configuration_request,
  "config": handle_config_request,
  "conversations": handle_conversations_request,
  "integrations": handle_integrations_request,
  "links": handle_links_request,
  "models": handle_models_request,
  "personas": handle_personas_request,
  "public_vars": handle_public_vars_request,
  "renewals": handle_renewals_request,
  "roles": handle_roles_request,
  "routes": handle_routes_request,
  "service_pages": handle_service_pages_request,
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
