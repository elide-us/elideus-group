"""Security OAuth registry helpers."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "relink_discord_request",
  "relink_google_request",
  "relink_microsoft_request",
  "register",
]

_DEF_PROVIDER = "security.oauth"
_PROVIDER_MODULE = "server.registry.security.oauth.mssql"
_PROVIDER_ATTRS: dict[str, str] = {
  "relink_discord": "relink_discord_v1",
  "relink_google": "relink_google_v1",
  "relink_microsoft": "relink_microsoft_v1",
}


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
  for name, attr in _PROVIDER_ATTRS.items():
    router.add_function(
      name,
      version=1,
      provider_map=f"{_DEF_PROVIDER}.{name}",
      provider=(_PROVIDER_MODULE, attr),
    )
