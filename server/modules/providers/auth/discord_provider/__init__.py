import aiohttp, base64, logging, uuid
from typing import Any, Dict

from fastapi import HTTPException, status

from server.modules.providers import AuthProviderBase

AUTHORIZE_URL = "https://discord.com/oauth2/authorize"
TOKEN_URL = "https://discord.com/api/oauth2/token"
USERINFO_URL = "https://discord.com/api/users/@me"


class DiscordAuthProvider(AuthProviderBase):
  """Discord OAuth provider."""
  requires_id_token = False

  def __init__(self, *, audience: str | None = None):
    super().__init__()
    self.audience = audience

  async def startup(self) -> None:
    logging.debug("[DiscordAuthProvider] startup")

  async def shutdown(self) -> None:
    logging.debug("[DiscordAuthProvider] shutdown")

  async def verify_id_token(self, id_token: str, access_token: str | None = None) -> Dict[str, Any]:
    token = access_token or id_token
    headers = {"Authorization": f"Bearer {token}"}
    async with aiohttp.ClientSession() as session:
      async with session.get(USERINFO_URL, headers=headers) as resp:
        if resp.status != 200:
          detail = await resp.text()
          raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
        return await resp.json()

  async def fetch_user_profile(self, access_token: str) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {access_token}"}
    async with aiohttp.ClientSession() as session:
      async with session.get(USERINFO_URL, headers=headers) as resp:
        if resp.status != 200:
          error = await resp.text()
          raise HTTPException(status_code=500, detail=f"Failed to fetch user profile: {error}")
        user = await resp.json()
      avatar_b64 = None
      avatar_hash = user.get("avatar")
      user_id = user.get("id")
      if avatar_hash and user_id:
        avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"
        try:
          async with session.get(avatar_url) as img_resp:
            if img_resp.status == 200:
              avatar_bytes = await img_resp.read()
              avatar_b64 = base64.b64encode(avatar_bytes).decode("utf-8")
        except Exception as e:
          logging.exception("[DiscordAuthProvider] failed to fetch avatar: %s", e)
    return {
      "email": user.get("email"),
      "username": user.get("username"),
      "profilePicture": avatar_b64,
    }

  def extract_guid(self, payload: Dict[str, Any]) -> str | None:
    user_id = payload.get("id")
    if not user_id:
      return None
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"discord:{user_id}"))
