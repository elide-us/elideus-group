"""System query handler package."""

from __future__ import annotations

from typing import Protocol, Sequence

from queryregistry.models import DBRequest, DBResponse

from .configuration.handler import handle_configuration_request
from .config.handler import handle_config_request
from .integrations.handler import handle_integrations_request
from .links.handler import handle_links_request
from .models.handler import handle_models_request
from .personas.handler import handle_personas_request
from .public_vars.handler import handle_public_vars_request
from .roles.handler import handle_roles_request
from .routes.handler import handle_routes_request
from .service_pages.handler import handle_service_pages_request

__all__ = ["HANDLERS"]

class _SubdomainHandler(Protocol):
  async def __call__(
    self,
    path: Sequence[str],
    request: DBRequest,
    *,
    provider: str,
  ) -> DBResponse: ...


HANDLERS: dict[str, _SubdomainHandler] = {
  "configuration": handle_configuration_request,
  "config": handle_config_request,
  "integrations": handle_integrations_request,
  "links": handle_links_request,
  "models": handle_models_request,
  "personas": handle_personas_request,
  "public_vars": handle_public_vars_request,
  "roles": handle_roles_request,
  "routes": handle_routes_request,
  "service_pages": handle_service_pages_request,
}
