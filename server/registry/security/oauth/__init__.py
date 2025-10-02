"""Security OAuth registry helpers."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from server.registry.types import DBRequest

from . import mssql  # noqa: F401

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "relink_discord_request",
  "relink_google_request",
  "relink_microsoft_request",
  "register",
]

_DEF_PROVIDER = "security.oauth"


def _relink_request(op: str, params: dict[str, Any]) -> DBRequest:
  return DBRequest(op=op, params=params)


def _common_params(
  *,
  provider_identifier: str,
  email: str,
  display_name: str,
  profile_image: str | None = None,
  confirm: bool | None = None,
  reauth_token: str | None = None,
) -> dict[str, Any]:
  payload: dict[str, Any] = {
    "provider_identifier": provider_identifier,
    "email": email,
    "display_name": display_name,
    "profile_image": profile_image or "",
  }
  if confirm is not None:
    payload["confirm"] = confirm
  if reauth_token is not None:
    payload["reauth_token"] = reauth_token
  return payload


def relink_discord_request(
  *,
  provider_identifier: str,
  email: str,
  display_name: str,
  profile_image: str | None = None,
  confirm: bool | None = None,
  reauth_token: str | None = None,
) -> DBRequest:
  return _relink_request(
    "db:security:oauth:relink_discord:1",
    _common_params(
      provider_identifier=provider_identifier,
      email=email,
      display_name=display_name,
      profile_image=profile_image,
      confirm=confirm,
      reauth_token=reauth_token,
    ),
  )


def relink_google_request(
  *,
  provider_identifier: str,
  email: str,
  display_name: str,
  profile_image: str | None = None,
  confirm: bool | None = None,
  reauth_token: str | None = None,
) -> DBRequest:
  return _relink_request(
    "db:security:oauth:relink_google:1",
    _common_params(
      provider_identifier=provider_identifier,
      email=email,
      display_name=display_name,
      profile_image=profile_image,
      confirm=confirm,
      reauth_token=reauth_token,
    ),
  )


def relink_microsoft_request(
  *,
  provider_identifier: str,
  email: str,
  display_name: str,
  profile_image: str | None = None,
  confirm: bool | None = None,
  reauth_token: str | None = None,
) -> DBRequest:
  return _relink_request(
    "db:security:oauth:relink_microsoft:1",
    _common_params(
      provider_identifier=provider_identifier,
      email=email,
      display_name=display_name,
      profile_image=profile_image,
      confirm=confirm,
      reauth_token=reauth_token,
    ),
  )


def register(router: "SubdomainRouter") -> None:
  router.add_function(
    "relink_discord",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.relink_discord",
  )
  router.add_function(
    "relink_google",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.relink_google",
  )
  router.add_function(
    "relink_microsoft",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.relink_microsoft",
  )
