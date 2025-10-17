"""Security OAuth registry helpers."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import DomainRouter

__all__ = [
  "relink_discord_request",
  "relink_google_request",
  "relink_microsoft_request",
  "register",
]


def _relink_request(provider: str, params: dict[str, Any]) -> DBRequest:
  return DBRequest(op=f"db:auth:{provider}:oauth_relink:1", params=params)


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
    "discord",
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
    "google",
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
    "microsoft",
    _common_params(
      provider_identifier=provider_identifier,
      email=email,
      display_name=display_name,
      profile_image=profile_image,
      confirm=confirm,
      reauth_token=reauth_token,
    ),
  )


def register(domain: "DomainRouter") -> None:
  domain.subdomain("discord").add_function(
    "oauth_relink",
    version=1,
    implementation="relink_discord",
  )
  domain.subdomain("google").add_function(
    "oauth_relink",
    version=1,
    implementation="relink_google",
  )
  domain.subdomain("microsoft").add_function(
    "oauth_relink",
    version=1,
    implementation="relink_microsoft",
  )
