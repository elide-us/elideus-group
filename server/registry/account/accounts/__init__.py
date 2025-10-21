"""Security account registry helpers."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "account_exists_request",
  "get_security_profile_request",
  "register",
]


def get_security_profile_request(
  *,
  guid: str | None = None,
  access_token: str | None = None,
  provider: str | None = None,
  provider_identifier: str | None = None,
  discord_id: str | None = None,
) -> DBRequest:
  params: dict[str, Any] = {}
  if guid is not None:
    params["guid"] = guid
  if access_token is not None:
    params["access_token"] = access_token
  if provider is not None:
    params["provider"] = provider
  if provider_identifier is not None:
    params["provider_identifier"] = provider_identifier
  if discord_id is not None:
    params["discord_id"] = discord_id
  return DBRequest(op="db:account:accounts:get_security_profile:1", params=params)


def account_exists_request(user_guid: str) -> DBRequest:
  return DBRequest(
    op="db:account:accounts:exists:1",
    params={"user_guid": user_guid},
  )


def register(
  router: "SubdomainRouter",
  *,
  legacy_op_segment: str | None = None,
) -> None:
  router.add_function("get_security_profile", version=1)
  router.add_function("account_exists", version=1)

  if legacy_op_segment:
    # Temporary compatibility alias while dependents migrate off singular ops.
    from server.registry import SubdomainRouter as _SubdomainRouter

    legacy_router = _SubdomainRouter(
      router._registry,
      router._domain,
      router._module_components,
      (legacy_op_segment,),
      provider=router._provider,
    )
    legacy_router.add_function(
      "get_security_profile",
      version=1,
      implementation="get_security_profile",
    )
    legacy_router.add_function(
      "account_exists",
      version=1,
      implementation="account_exists",
    )
