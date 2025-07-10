import os, aiohttp, base64
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from typing import Dict, Optional
from . import BaseModule

async def fetch_ms_jwks_uri() -> str:
  async with aiohttp.ClientSession() as session:
    async with session.get("https://login.microsoftonline.com/consumers/v2.0/.well-known/openid-configuration") as response:
      if response.status != 200:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to fetch OpenID configuration.")
      data = await response.json()
      return data["jwks_uri"]

async def fetch_ms_jwks(jwks_uri: str) -> Dict:
  async with aiohttp.ClientSession() as session:
    async with session.get(jwks_uri) as response:
      if response.status != 200:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to fetch JWKS.")
      return await response.json()

class AuthModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.ms_jwks: Optional[Dict] = None
    self.ms_api_id: Optional[str] = os.getenv("MS_API_ID")
    self.jwt_secret: str = os.getenv("JWT_SECRET", "secret")
    self.jwt_algo_ms: str = "RS256"
    self.jwt_algo_int: str = "HS256"

  async def startup(self):
    try:
      jwks_uri = await fetch_ms_jwks_uri()
      self.ms_jwks = await fetch_ms_jwks(jwks_uri)
    except Exception as e:
      print(f"[AuthModule] Failed to load Microsoft JWKS: {e}")

  async def shutdown(self):
    pass

  async def verify_ms_id_token(self, id_token: str) -> Dict:
    if not self.ms_jwks:
      raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Microsoft keys unavailable")
    try:
      unverified_header = jwt.get_unverified_header(id_token)
    except Exception:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ID token.")
    rsa_key = next(
      ({
        "kty": key["kty"],
        "kid": key["kid"],
        "use": key["use"],
        "n": key["n"],
        "e": key["e"],
      } for key in self.ms_jwks.get("keys", []) if key["kid"] == unverified_header["kid"]),
      None,
    )
    if not rsa_key:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token header.")
    try:
      payload = jwt.decode(
        id_token,
        rsa_key,
        algorithms=[self.jwt_algo_ms],
        audience=self.ms_api_id,
        issuer="https://login.microsoftonline.com/9188040d-6c67-4c5b-b112-36a304b66dad/v2.0",
      )
      return payload
    except jwt.ExpiredSignatureError:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired.")
    except jwt.JWTClaimsError:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect claims. Please check the audience and issuer.")
    except Exception:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token validation failed.")

  async def fetch_ms_user_profile(self, access_token: str) -> Dict:
    async with aiohttp.ClientSession() as session:
      headers = {"Authorization": f"Bearer {access_token}"}
      async with session.get("https://graph.microsoft.com/v1.0/me", headers=headers) as response:
        if response.status != 200:
          error_message = await response.text()
          raise HTTPException(status_code=500, detail=f"Failed to fetch user profile. Status: {response.status}, Error: {error_message}")
        user = await response.json()
      profile_picture_base64 = None
      async with session.get("https://graph.microsoft.com/v1.0/me/photo/$value", headers=headers) as response:
        if response.status == 200:
          picture_bytes = await response.read()
          profile_picture_base64 = base64.b64encode(picture_bytes).decode("utf-8")
      return {
        "email": user.get("mail") or user.get("userPrincipalName"),
        "username": user.get("displayName"),
        "profilePicture": profile_picture_base64,
      }

  async def handle_ms_auth_login(self, id_token: str, access_token: str):
    payload = await self.verify_ms_id_token(id_token)
    guid = payload.get("sub")
    if not guid:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")
    profile = await self.fetch_ms_user_profile(access_token)
    return guid, profile

  def make_bearer_token(self, guid: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=24)
    token_data = {"sub": guid, "exp": exp.timestamp()}
    token = jwt.encode(token_data, self.jwt_secret, algorithm=self.jwt_algo_int)
    return token

  async def decode_bearer_token(self, token: str) -> Dict:
    try:
      payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algo_int])
    except JWTError:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})
    exp = payload.get("exp")
    if not exp:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expiry not found", headers={"WWW-Authenticate": "Bearer"})
    if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired", headers={"WWW-Authenticate": "Bearer"})
    sub = payload.get("sub")
    if not sub:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Subject not found", headers={"WWW-Authenticate": "Bearer"})
    return {"guid": sub}

  async def get_bearer_token_payload(self, request: Request, token: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    return await self.decode_bearer_token(token.credentials)
