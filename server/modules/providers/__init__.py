"""Provider contract definitions for authentication and database layers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from enum import Enum

import aiohttp
from fastapi import HTTPException, status
from jose import jwt
import logging

from pydantic import BaseModel

__all__ = [
  "AuthProvider",
  "BaseProvider",
  "LifecycleProvider",
  "AuthProviderBase",
  "DbProviderBase",
  "DBResult",
  "DbRunMode",
]


class DBResult(BaseModel):
  rows: list[dict] = []
  rowcount: int = 0


class DbRunMode(str, Enum):
  ROW_ONE = "row_one"
  ROW_MANY = "row_many"
  JSON_ONE = "json_one"
  JSON_MANY = "json_many"
  EXEC = "exec"


class BaseProvider(ABC):
  def __init__(self, **config: Any):
    self.config = config


class LifecycleProvider(BaseProvider):
  @abstractmethod
  async def startup(self) -> None: ...

  @abstractmethod
  async def shutdown(self) -> None: ...


class AuthProviderBase(LifecycleProvider):
  requires_id_token = True

  @abstractmethod
  async def verify_id_token(self, id_token: str | None, access_token: str | None = None) -> Dict[str, Any]: ...

  @abstractmethod
  async def fetch_user_profile(self, access_token: str) -> Dict[str, Any]: ...

  @abstractmethod
  def extract_guid(self, payload: Dict[str, Any]) -> str | None: ...


class DbProviderBase(LifecycleProvider):
  @abstractmethod
  async def run(self, op: str, args: Dict[str, Any]) -> DBResult: ...


class AuthProvider(AuthProviderBase):
  def __init__(self, *, audience: str, issuer: str, jwks_uri: str, algorithm: str = "RS256", jwks_expiry: timedelta | None = None):
    super().__init__()
    self.audience = audience
    self.issuer = issuer
    self.jwks_uri = jwks_uri
    self.algorithm = algorithm
    self.jwks_expiry = jwks_expiry or timedelta(hours=1)
    self._jwks: Dict[str, Any] | None = None
    self._jwks_fetched_at: datetime | None = None

  async def startup(self) -> None:
    logging.debug("[AuthProvider] Startup initiating JWKS fetch")
    await self._get_jwks()

  async def shutdown(self) -> None:
    pass

  async def fetch_jwks(self):
    logging.debug("[AuthProvider] Fetching JWKS from %s", self.jwks_uri)
    async with aiohttp.ClientSession() as session:
      async with session.get(self.jwks_uri) as response:
        if response.status != 200:
          raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to fetch JWKS.")
        self._jwks = await response.json()
        self._jwks_fetched_at = datetime.now(timezone.utc)
        logging.debug("[AuthProvider] JWKS fetched")

  async def _get_jwks(self) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    if not self._jwks or not self._jwks_fetched_at or now - self._jwks_fetched_at > self.jwks_expiry:
      logging.debug("[AuthProvider] JWKS cache miss or expired")
      await self.fetch_jwks()
    else:
      logging.debug("[AuthProvider] Using cached JWKS")
    return self._jwks

  async def verify_id_token(self, id_token: str | None, access_token: str | None = None) -> Dict[str, Any]:
    if not id_token:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ID token.")
    logging.debug("[AuthProvider] Verifying ID token %s", id_token[:40])
    jwks = await self._get_jwks()
    try:
      unverified_header = jwt.get_unverified_header(id_token)
    except Exception:
      logging.debug("[AuthProvider] Failed to parse token header")
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
      decode_kwargs = {
        "algorithms": [self.algorithm],
        "audience": self.audience,
        "issuer": self.issuer,
      }
      if access_token:
        decode_kwargs["access_token"] = access_token
      payload = jwt.decode(id_token, rsa_key, **decode_kwargs)
      logging.debug("[AuthProvider] ID token verified for audience=%s", self.audience)
      return payload
    except jwt.ExpiredSignatureError:
      logging.debug("[AuthProvider] ID token expired")
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired.")
    except jwt.JWTClaimsError:
      logging.debug("[AuthProvider] ID token claims error")
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect claims. Please check the audience and issuer.")
    except Exception:
      logging.debug("[AuthProvider] ID token validation failed")
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token validation failed.")

  async def fetch_user_profile(self, access_token: str) -> Dict[str, Any]:
    raise NotImplementedError

  def extract_guid(self, payload: Dict[str, Any]) -> str | None:
    return payload.get("sub")
