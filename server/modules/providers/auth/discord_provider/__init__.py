from typing import Any, Dict

from fastapi import HTTPException, status

from server.modules.providers import AuthProviderBase


class DiscordAuthProvider(AuthProviderBase):
  requires_id_token = False
  """Placeholder Discord OAuth provider.

  This provider will handle Discord's OAuth flow and user profile retrieval
  once implemented. Discord does not issue an ID token, so verification logic
  will need to be tailored for access tokens and the Discord API.
  """

  async def startup(self) -> None:
    """Initialize any resources required for Discord OAuth.

    TODO: Fetch and cache Discord configuration details if necessary.
    """
    return None

  async def shutdown(self) -> None:
    """Clean up any resources allocated during startup."""
    return None

  async def verify_id_token(self, id_token: str, access_token: str | None = None) -> Dict[str, Any]:
    """Discord does not provide JWT ID tokens.

    This method will validate access tokens when the implementation is
    completed.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Discord token verification not implemented")

  async def fetch_user_profile(self, access_token: str) -> Dict[str, Any]:
    """Retrieve the user's Discord profile using the provided access token."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Discord profile fetch not implemented")

  def extract_guid(self, payload: Dict[str, Any]) -> str | None:
    """Return the normalized Discord user identifier.

    TODO: Normalize the 'id' field or any other unique identifier returned by
    Discord once the payload structure is defined.
    """
    return payload.get("id")
