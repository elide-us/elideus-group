import aiohttp
import base64
import uuid
from datetime import timedelta
from typing import Dict, Any

from fastapi import HTTPException, status
import logging

from server.modules.providers import AuthProvider

GOOGLE_OPENID_CONFIG = "https://accounts.google.com/.well-known/openid-configuration"
GOOGLE_ISSUER = "https://accounts.google.com"


async def _fetch_openid_config() -> Dict[str, Any]:
  logging.debug("[GoogleAuthProvider] Fetching OpenID configuration from %s", GOOGLE_OPENID_CONFIG)
  async with aiohttp.ClientSession() as session:
    async with session.get(GOOGLE_OPENID_CONFIG) as response:
      if response.status != 200:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to fetch OpenID configuration.")
      config = await response.json()
      logging.debug("[GoogleAuthProvider] OpenID configuration fetched")
      return config


class GoogleAuthProvider(AuthProvider):
  def __init__(self, *, api_id: str, jwks_uri: str, jwks_expiry: timedelta):
    super().__init__(audience=api_id, issuer=GOOGLE_ISSUER, jwks_uri=jwks_uri, jwks_expiry=jwks_expiry)
    self.userinfo_endpoint: str | None = None

  @classmethod
  async def create(cls, *, api_id: str, jwks_expiry: timedelta):
    logging.debug("[GoogleAuthProvider] Creating provider with api_id=%s", api_id)
    config = await _fetch_openid_config()
    jwks_uri = config["jwks_uri"]
    userinfo_endpoint = config.get("userinfo_endpoint")
    logging.debug(
      "[GoogleAuthProvider] jwks_uri=%s userinfo_endpoint=%s jwks_expiry=%s",
      jwks_uri,
      userinfo_endpoint,
      jwks_expiry,
    )
    provider = cls(api_id=api_id, jwks_uri=jwks_uri, jwks_expiry=jwks_expiry)
    provider.userinfo_endpoint = userinfo_endpoint
    return provider

  async def fetch_user_profile(self, access_token: str) -> Dict[str, Any]:
    if not self.userinfo_endpoint:
      raise HTTPException(status_code=500, detail="Userinfo endpoint not configured")
    logging.debug("[GoogleAuthProvider] Fetching user profile from %s", self.userinfo_endpoint)
    logging.debug("[GoogleAuthProvider] access_token=%s", access_token[:40])
    async with aiohttp.ClientSession() as session:
      headers = {"Authorization": f"Bearer {access_token}"}
      async with session.get(self.userinfo_endpoint, headers=headers) as response:
        if response.status != 200:
          error_message = await response.text()
          raise HTTPException(status_code=500, detail=f"Failed to fetch user profile. Status: {response.status}, Error: {error_message}")
        user = await response.json()
      profile_picture_base64 = None
      picture_url = user.get("picture")
      if picture_url:
        try:
          async with session.get(picture_url) as img_resp:
            if img_resp.status == 200:
              picture_bytes = await img_resp.read()
              profile_picture_base64 = base64.b64encode(picture_bytes).decode("utf-8")
        except Exception as e:
          logging.exception("[GoogleAuthProvider] failed to fetch profile image: %s", e)
    return {
      "email": user.get("email"),
      "username": user.get("name"),
      "profilePicture": profile_picture_base64,
    }

  def extract_guid(self, payload: Dict[str, Any]) -> str | None:
    guid = payload.get("sub")
    if not guid:
      return None
    try:
      return str(uuid.UUID(guid))
    except ValueError:
      return str(uuid.uuid5(uuid.NAMESPACE_URL, guid))
