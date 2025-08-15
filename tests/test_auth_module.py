import asyncio
from fastapi import FastAPI
from datetime import datetime, timedelta, timezone

from server.modules import auth_module
from server.modules.auth_module import AuthModule


def test_verify_ms_id_token_refreshes_jwks(monkeypatch):
  app = FastAPI()
  module = AuthModule(app)
  module.ms_jwks = {"keys": [{"kid": "kid1", "kty": "RSA", "use": "sig", "n": "n", "e": "e"}]}
  module.ms_jwks_fetched_at = datetime.now(timezone.utc) - timedelta(hours=2)
  module.ms_api_id = "api"

  async def fake_fetch_ms_jwks_uri():
    return "uri"

  async def fake_fetch_ms_jwks(uri):
    return {"keys": [{"kid": "kid1", "kty": "RSA", "use": "sig", "n": "n", "e": "e"}]}

  monkeypatch.setattr(auth_module, "fetch_ms_jwks_uri", fake_fetch_ms_jwks_uri)
  monkeypatch.setattr(auth_module, "fetch_ms_jwks", fake_fetch_ms_jwks)

  def fake_get_unverified_header(token):
    return {"kid": "kid1"}

  def fake_decode(token, key, algorithms, audience, issuer):
    return {"sub": "123"}

  monkeypatch.setattr(auth_module.jwt, "get_unverified_header", fake_get_unverified_header)
  monkeypatch.setattr(auth_module.jwt, "decode", fake_decode)

  asyncio.run(module.verify_ms_id_token("token"))
  assert module.ms_jwks_fetched_at > datetime.now(timezone.utc) - timedelta(minutes=5)


def test_handle_auth_login_prefers_oid(monkeypatch):
  app = FastAPI()
  module = AuthModule(app)

  async def fake_verify_ms_id_token(token):
    return {"oid": "oid123", "sub": "sub456"}

  async def fake_fetch_ms_user_profile(token):
    return {"email": "user@example.com", "username": "User"}

  monkeypatch.setattr(module, "verify_ms_id_token", fake_verify_ms_id_token)
  monkeypatch.setattr(module, "fetch_ms_user_profile", fake_fetch_ms_user_profile)

  guid, profile = asyncio.run(module.handle_auth_login("microsoft", "id", "access"))
  assert guid == "oid123"
  assert profile["email"] == "user@example.com"


def test_handle_auth_login_falls_back_to_sub(monkeypatch):
  app = FastAPI()
  module = AuthModule(app)

  async def fake_verify_ms_id_token(token):
    return {"sub": "sub456"}

  async def fake_fetch_ms_user_profile(token):
    return {"email": "user@example.com", "username": "User"}

  monkeypatch.setattr(module, "verify_ms_id_token", fake_verify_ms_id_token)
  monkeypatch.setattr(module, "fetch_ms_user_profile", fake_fetch_ms_user_profile)

  guid, _ = asyncio.run(module.handle_auth_login("microsoft", "id", "access"))
  assert guid == "sub456"
