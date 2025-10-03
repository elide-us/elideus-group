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

_DEF_PROVIDER = "security.accounts"
_PROVIDER_MODULE = "server.registry.security.accounts.mssql"
_PROVIDER_ATTRS: dict[str, str] = {
  "get_security_profile": "get_security_profile_v1",
  "account_exists": "account_exists_v1",
}


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
  return DBRequest(op="db:security:accounts:get_security_profile:1", params=params)


def account_exists_request(user_guid: str) -> DBRequest:
  return DBRequest(
    op="db:security:accounts:account_exists:1",
    params={"user_guid": user_guid},
  )


def register(router: "SubdomainRouter") -> None:
  for name, attr in _PROVIDER_ATTRS.items():
    router.add_function(
      name,
      version=1,
      provider_map=f"{_DEF_PROVIDER}.{name}",
      provider=(_PROVIDER_MODULE, attr),
    )
