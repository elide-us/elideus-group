import asyncio, logging
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI, HTTPException, status

from server.modules.auth_module import AuthModule
import server.modules.providers as providers
from server.modules.providers.microsoft import MicrosoftAuthProvider


def test_verify_id_token_expired_logs_error(monkeypatch, caplog):
  caplog.set_level(logging.ERROR)
  provider = MicrosoftAuthProvider(api_id="api", jwks_uri="uri", jwks_expiry=timedelta(minutes=5))
  provider._jwks = {"keys": [{"kid": "kid1", "kty": "RSA", "use": "sig", "n": "n", "e": "e"}]}
  provider._jwks_fetched_at = datetime.now(timezone.utc)

  def fake_get_unverified_header(token):
    return {"kid": "kid1"}

  def fake_decode(token, key, algorithms, audience, issuer):
    logging.error("expired token")
    raise providers.jwt.ExpiredSignatureError()

  monkeypatch.setattr(providers.jwt, "get_unverified_header", fake_get_unverified_header)
  monkeypatch.setattr(providers.jwt, "decode", fake_decode)

  with pytest.raises(HTTPException) as exc:
    asyncio.run(provider.verify_id_token("token"))
  assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
  assert any("expired token" in r.message for r in caplog.records)


def test_verify_id_token_invalid_logs_error(monkeypatch, caplog):
  caplog.set_level(logging.ERROR)
  provider = MicrosoftAuthProvider(api_id="api", jwks_uri="uri", jwks_expiry=timedelta(minutes=5))
  provider._jwks = {"keys": []}
  provider._jwks_fetched_at = datetime.now(timezone.utc)

  def fake_get_unverified_header(token):
    logging.error("invalid token header")
    raise Exception("bad header")

  monkeypatch.setattr(providers.jwt, "get_unverified_header", fake_get_unverified_header)

  with pytest.raises(HTTPException) as exc:
    asyncio.run(provider.verify_id_token("bad"))
  assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
  assert any("invalid token header" in r.message for r in caplog.records)


def test_verify_id_token_handles_jwks_rotation(monkeypatch, caplog):
  caplog.set_level(logging.INFO)
  provider = MicrosoftAuthProvider(api_id="api", jwks_uri="uri", jwks_expiry=timedelta(minutes=1))
  provider._jwks = {"keys": [{"kid": "old", "kty": "RSA", "use": "sig", "n": "n", "e": "e"}]}
  provider._jwks_fetched_at = datetime.now(timezone.utc) - timedelta(minutes=2)

  async def fake_fetch_jwks():
    logging.info("jwks rotated")
    provider._jwks = {"keys": [{"kid": "new", "kty": "RSA", "use": "sig", "n": "n", "e": "e"}]}
    provider._jwks_fetched_at = datetime.now(timezone.utc)

  monkeypatch.setattr(provider, "fetch_jwks", fake_fetch_jwks)

  def fake_get_unverified_header(token):
    return {"kid": "new"}

  def fake_decode(token, key, algorithms, audience, issuer):
    return {"sub": "123"}

  monkeypatch.setattr(providers.jwt, "get_unverified_header", fake_get_unverified_header)
  monkeypatch.setattr(providers.jwt, "decode", fake_decode)

  asyncio.run(provider.verify_id_token("token"))
  assert provider._jwks["keys"][0]["kid"] == "new"
  assert any("jwks rotated" in r.message for r in caplog.records)


def test_handle_auth_login_network_failure(monkeypatch, caplog):
  caplog.set_level(logging.ERROR)
  app = FastAPI()
  module = AuthModule(app)

  class FakeProvider:
    async def verify_id_token(self, token):
      return {"sub": "abc"}

    async def fetch_user_profile(self, token):
      logging.error("network failure")
      raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="network")

    def extract_guid(self, payload):
      return payload.get("sub")

  module.providers["microsoft"] = FakeProvider()

  with pytest.raises(HTTPException) as exc:
    asyncio.run(module.handle_auth_login("microsoft", "id", "access"))
  assert exc.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
  assert any("network failure" in r.message for r in caplog.records)

