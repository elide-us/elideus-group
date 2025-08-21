import aiohttp
from datetime import timedelta
from typing import Dict, Any

from fastapi import HTTPException, status

from server.modules.providers import AuthProvider

GOOGLE_OPENID_CONFIG = "https://accounts.google.com/.well-known/openid-configuration"
GOOGLE_ISSUER = "https://accounts.google.com"


async def _fetch_openid_config() -> Dict[str, Any]:
  async with aiohttp.ClientSession() as session:
    async with session.get(GOOGLE_OPENID_CONFIG) as response:
      if response.status != 200:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to fetch OpenID configuration.")
      return await response.json()


class GoogleAuthProvider(AuthProvider):
  def __init__(self, *, api_id: str, jwks_uri: str, jwks_expiry: timedelta):
    super().__init__(audience=api_id, issuer=GOOGLE_ISSUER, jwks_uri=jwks_uri, jwks_expiry=jwks_expiry)
    self.userinfo_endpoint: str | None = None

  @classmethod
  async def create(cls, *, api_id: str, jwks_expiry: timedelta):
    config = await _fetch_openid_config()
    jwks_uri = config["jwks_uri"]
    provider = cls(api_id=api_id, jwks_uri=jwks_uri, jwks_expiry=jwks_expiry)
    provider.userinfo_endpoint = config.get("userinfo_endpoint")
    return provider

  async def fetch_user_profile(self, access_token: str) -> Dict[str, Any]:
    if not self.userinfo_endpoint:
      raise HTTPException(status_code=500, detail="Userinfo endpoint not configured")
    async with aiohttp.ClientSession() as session:
      headers = {"Authorization": f"Bearer {access_token}"}
      async with session.get(self.userinfo_endpoint, headers=headers) as response:
        if response.status != 200:
          error_message = await response.text()
          raise HTTPException(status_code=500, detail=f"Failed to fetch user profile. Status: {response.status}, Error: {error_message}")
        user = await response.json()
      return {
        "email": user.get("email"),
        "username": user.get("name"),
        "profilePicture": user.get("picture"),
      }
