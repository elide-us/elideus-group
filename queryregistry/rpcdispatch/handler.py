"""RPC dispatch domain handler implementations."""

from __future__ import annotations

from typing import Sequence

from fastapi import HTTPException

from queryregistry.models import DBRequest, DBResponse

from .domains.handler import handle_domains_request
from .subdomains.handler import handle_subdomains_request
from .functions.handler import handle_functions_request
from .models.handler import handle_models_request
from .model_fields.handler import handle_model_fields_request

__all__ = ["handle_rpcdispatch_request"]

HANDLERS = {
  "domains": handle_domains_request,
  "subdomains": handle_subdomains_request,
  "functions": handle_functions_request,
  "models": handle_models_request,
  "model_fields": handle_model_fields_request,
}


async def handle_rpcdispatch_request(path: Sequence[str], request: DBRequest, *, provider: str) -> DBResponse:
  if not path:
    raise HTTPException(status_code=404, detail="Unknown rpcdispatch registry operation")
  handler = HANDLERS.get(path[0])
  if handler is None:
    raise HTTPException(status_code=404, detail="Unknown rpcdispatch registry operation")
  return await handler(path[1:], request, provider=provider)
