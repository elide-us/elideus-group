import asyncio
import importlib.util
import pathlib
import sys
import types
import pytest
from fastapi import FastAPI, HTTPException, status
from datetime import datetime, timedelta, timezone

# stub server package to avoid importing server.__init__
root_path = pathlib.Path(__file__).resolve().parent.parent
server_pkg = types.ModuleType("server")
server_pkg.__path__ = [str(root_path / "server")]
sys.modules.setdefault("server", server_pkg)
modules_pkg = types.ModuleType("server.modules")
modules_pkg.__path__ = [str(root_path / "server/modules")]
class BaseModule:
  def __init__(self, app):
    self.app = app
  async def startup(self):
    pass
  async def shutdown(self):
    pass
  def mark_ready(self):
    pass
  async def on_ready(self):
    pass
modules_pkg.BaseModule = BaseModule
sys.modules.setdefault("server.modules", modules_pkg)

spec_auth = importlib.util.spec_from_file_location(
  "server.modules.auth_module", root_path / "server/modules/auth_module.py"
)
auth_module = importlib.util.module_from_spec(spec_auth)
spec_auth.loader.exec_module(auth_module)
AuthModule = auth_module.AuthModule

spec_providers = importlib.util.spec_from_file_location(
  "server.modules.providers", root_path / "server/modules/providers/__init__.py"
)
providers = importlib.util.module_from_spec(spec_providers)
spec_providers.loader.exec_module(providers)
sys.modules["server.modules.providers"] = providers

spec_ms = importlib.util.spec_from_file_location(
  "server.modules.providers.auth.microsoft_provider",
  root_path / "server/modules/providers/auth/microsoft_provider/__init__.py",
)
ms_provider = importlib.util.module_from_spec(spec_ms)
spec_ms.loader.exec_module(ms_provider)
sys.modules["server.modules.providers.auth.microsoft_provider"] = ms_provider
MicrosoftAuthProvider = ms_provider.MicrosoftAuthProvider


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

  monkeypatch.setattr(providers.jwt, "get_unverified_header", fake_get_unverified_header)
  monkeypatch.setattr(providers.jwt, "decode", fake_decode)

  asyncio.run(provider.verify_id_token("token"))
  assert provider._jwks_fetched_at > datetime.now(timezone.utc) - timedelta(minutes=5)


def test_handle_auth_login_prefers_oid(monkeypatch):
  app = FastAPI()
  module = AuthModule(app)

  class FakeProvider:
    async def verify_id_token(self, token, access_token):
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
    async def verify_id_token(self, token, access_token):
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

    async def verify_id_token(self, token, access_token):
      self.called = True
      return {"sub": "a"}

    async def fetch_user_profile(self, token):
      return {"email": "a@example.com", "username": "A"}

    def extract_guid(self, payload):
      return payload.get("sub")

  class ProviderB(ProviderA):
    async def verify_id_token(self, token, access_token):
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
