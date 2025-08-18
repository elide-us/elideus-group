from datetime import datetime, timedelta, timezone
from typing import Dict, Any

import aiohttp
from fastapi import HTTPException, status
from jose import jwt

class AuthProvider:
  def __init__(self, *, audience: str, issuer: str, jwks_uri: str, algorithm: str = "RS256", jwks_expiry: timedelta | None = None):
    self.audience = audience
    self.issuer = issuer
    self.jwks_uri = jwks_uri
    self.algorithm = algorithm
    self.jwks_expiry = jwks_expiry or timedelta(hours=1)
    self._jwks: Dict[str, Any] | None = None
    self._jwks_fetched_at: datetime | None = None

  async def fetch_jwks(self):
    async with aiohttp.ClientSession() as session:
      async with session.get(self.jwks_uri) as response:
        if response.status != 200:
          raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to fetch JWKS.")
        self._jwks = await response.json()
        self._jwks_fetched_at = datetime.now(timezone.utc)

  async def _get_jwks(self) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    if not self._jwks or not self._jwks_fetched_at or now - self._jwks_fetched_at > self.jwks_expiry:
      await self.fetch_jwks()
    return self._jwks

  async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
    jwks = await self._get_jwks()
    try:
      unverified_header = jwt.get_unverified_header(id_token)
    except Exception:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ID token.")
    rsa_key = next(({
      "kty": key["kty"],
      "kid": key["kid"],
      "use": key["use"],
      "n": key["n"],
      "e": key["e"],
    } for key in jwks.get("keys", []) if key["kid"] == unverified_header["kid"]), None)
    if not rsa_key:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token header.")
    try:
      payload = jwt.decode(id_token, rsa_key, algorithms=[self.algorithm], audience=self.audience, issuer=self.issuer)
      return payload
    except jwt.ExpiredSignatureError:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired.")
    except jwt.JWTClaimsError:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect claims. Please check the audience and issuer.")
    except Exception:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token validation failed.")

  async def fetch_user_profile(self, access_token: str) -> Dict[str, Any]:
    raise NotImplementedError

  def extract_guid(self, payload: Dict[str, Any]) -> str | None:
    return payload.get("sub")
