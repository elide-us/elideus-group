"""System query handler package."""

from __future__ import annotations

from typing import Protocol, Sequence

from server.queryregistry.models import DBRequest, DBResponse

from .configuration.handler import handle_configuration_request

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
}
