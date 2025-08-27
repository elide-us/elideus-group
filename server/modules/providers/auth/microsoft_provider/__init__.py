import base64
from datetime import timedelta
from typing import Dict, Any

import aiohttp

from fastapi import HTTPException, status
from server.modules.providers import AuthProvider

MICROSOFT_OPENID_CONFIG = "https://login.microsoftonline.com/consumers/v2.0/.well-known/openid-configuration"
MICROSOFT_GRAPH_USER = "https://graph.microsoft.com/v1.0/me"
MICROSOFT_GRAPH_PHOTO = "https://graph.microsoft.com/v1.0/me/photo/$value"
MICROSOFT_ISSUER = "https://login.microsoftonline.com/9188040d-6c67-4c5b-b112-36a304b66dad/v2.0"

async def _fetch_openid_config() -> Dict[str, Any]:
  async with aiohttp.ClientSession() as session:
    async with session.get(MICROSOFT_OPENID_CONFIG) as response:
      if response.status != 200:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to fetch OpenID configuration.")
      return await response.json()

class MicrosoftAuthProvider(AuthProvider):
  def __init__(self, *, api_id: str, jwks_uri: str, jwks_expiry: timedelta):
    super().__init__(audience=api_id, issuer=MICROSOFT_ISSUER, jwks_uri=jwks_uri, jwks_expiry=jwks_expiry)

  @classmethod
  async def create(cls, *, api_id: str, jwks_expiry: timedelta):
    config = await _fetch_openid_config()
    jwks_uri = config["jwks_uri"]
    return cls(api_id=api_id, jwks_uri=jwks_uri, jwks_expiry=jwks_expiry)

  async def fetch_user_profile(self, access_token: str) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
      headers = {"Authorization": f"Bearer {access_token}"}
      async with session.get(MICROSOFT_GRAPH_USER, headers=headers) as response:
        if response.status != 200:
          error_message = await response.text()
          raise HTTPException(status_code=500, detail=f"Failed to fetch user profile. Status: {response.status}, Error: {error_message}")
        user = await response.json()
      profile_picture_base64 = None
      async with session.get(MICROSOFT_GRAPH_PHOTO, headers=headers) as response:
        if response.status == 200:
          picture_bytes = await response.read()
          profile_picture_base64 = base64.b64encode(picture_bytes).decode("utf-8")
      return {
        "email": user.get("mail") or user.get("userPrincipalName"),
        "username": user.get("displayName"),
        "profilePicture": profile_picture_base64,
      }

  def extract_guid(self, payload: Dict[str, Any]) -> str | None:
    return payload.get("oid") or payload.get("sub")
