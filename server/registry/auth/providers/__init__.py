"""Authentication provider registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "register",
  "unlink_last_provider_request",
]


def unlink_last_provider_request(*, guid: str, provider: str) -> DBRequest:
  return DBRequest(
    op="db:auth:providers:unlink_last_provider:1",
    params={"guid": guid, "provider": provider},
  )


def register(router: "SubdomainRouter") -> None:
  router.add_function("unlink_last_provider", version=1)
