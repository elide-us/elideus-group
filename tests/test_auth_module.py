import asyncio
import pytest
from fastapi import FastAPI, HTTPException, status
from datetime import datetime, timedelta, timezone

from server.modules.auth_module import AuthModule
from server.modules.providers import auth_base
from server.modules.providers.microsoft import MicrosoftAuthProvider


def test_verify_id_token_refreshes_jwks(monkeypatch):
  provider = MicrosoftAuthProvider(api_id="api", jwks_uri="uri", jwks_expiry=timedelta(minutes=60))
  provider._jwks = {"keys": [{"kid": "kid1", "kty": "RSA", "use": "sig", "n": "n", "e": "e"}]}
  provider._jwks_fetched_at = datetime.now(timezone.utc) - timedelta(hours=2)

  async def fake_fetch_jwks():
    provider._jwks = {"keys": [{"kid": "kid1", "kty": "RSA", "use": "sig", "n": "n", "e": "e"}]}
    provider._jwks_fetched_at = datetime.now(timezone.utc)

  monkeypatch.setattr(provider, "fetch_jwks", fake_fetch_jwks)

  def fake_get_unverified_header(token):
    return {"kid": "kid1"}

  def fake_decode(token, key, algorithms, audience, issuer):
    return {"sub": "123"}

  monkeypatch.setattr(auth_base.jwt, "get_unverified_header", fake_get_unverified_header)
  monkeypatch.setattr(auth_base.jwt, "decode", fake_decode)

  asyncio.run(provider.verify_id_token("token"))
  assert provider._jwks_fetched_at > datetime.now(timezone.utc) - timedelta(minutes=5)


def test_handle_auth_login_prefers_oid(monkeypatch):
  app = FastAPI()
  module = AuthModule(app)

  class FakeProvider:
    async def verify_id_token(self, token):
      return {"oid": "oid123", "sub": "sub456"}

    async def fetch_user_profile(self, token):
      return {"email": "user@example.com", "username": "User"}

    def extract_guid(self, payload):
      return payload.get("oid") or payload.get("sub")

  module.providers["microsoft"] = FakeProvider()

  guid, profile, payload = asyncio.run(module.handle_auth_login("microsoft", "id", "access"))
  assert guid == "oid123"
  assert profile["email"] == "user@example.com"
  assert payload["oid"] == "oid123"
  assert payload["sub"] == "sub456"


def test_handle_auth_login_falls_back_to_sub(monkeypatch):
  app = FastAPI()
  module = AuthModule(app)

  class FakeProvider:
    async def verify_id_token(self, token):
      return {"sub": "sub456"}

    async def fetch_user_profile(self, token):
      return {"email": "user@example.com", "username": "User"}

    def extract_guid(self, payload):
      return payload.get("oid") or payload.get("sub")

  module.providers["microsoft"] = FakeProvider()

  guid, _, payload = asyncio.run(module.handle_auth_login("microsoft", "id", "access"))
  assert guid == "sub456"
  assert payload["sub"] == "sub456"


def test_handle_auth_login_selects_provider():
  app = FastAPI()
  module = AuthModule(app)

  class ProviderA:
    def __init__(self):
      self.called = False

    async def verify_id_token(self, token):
      self.called = True
      return {"sub": "a"}

    async def fetch_user_profile(self, token):
      return {"email": "a@example.com", "username": "A"}

    def extract_guid(self, payload):
      return payload.get("sub")

  class ProviderB(ProviderA):
    async def verify_id_token(self, token):
      self.called = True
      return {"sub": "b"}

    async def fetch_user_profile(self, token):
      return {"email": "b@example.com", "username": "B"}

  module.providers["a"] = ProviderA()
  module.providers["b"] = ProviderB()

  guid, profile, _ = asyncio.run(module.handle_auth_login("b", "id", "access"))
  assert guid == "b"
  assert profile["username"] == "B"
  assert module.providers["b"].called is True
  assert module.providers["a"].called is False


def test_jwks_refresh_failure(monkeypatch):
  provider = MicrosoftAuthProvider(api_id="api", jwks_uri="uri", jwks_expiry=timedelta(minutes=1))
  provider._jwks = {"keys": []}
  provider._jwks_fetched_at = datetime.now(timezone.utc) - timedelta(hours=2)

  async def fake_fetch_jwks():
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="fail")

  monkeypatch.setattr(provider, "fetch_jwks", fake_fetch_jwks)

  with pytest.raises(HTTPException) as exc:
    asyncio.run(provider.verify_id_token("token"))

  assert exc.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
