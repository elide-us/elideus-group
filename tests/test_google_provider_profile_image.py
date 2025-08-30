import asyncio
import base64
import types
from datetime import timedelta

from server.modules.providers.auth import google_provider


def test_fetch_user_profile_downloads_image(monkeypatch):
  provider = google_provider.GoogleAuthProvider(
    api_id="gid", jwks_uri="uri", jwks_expiry=timedelta(minutes=1)
  )
  provider.userinfo_endpoint = "userinfo"

  class DummyResp:
    def __init__(self, status, data, is_json=False):
      self.status = status
      self.data = data
      self.is_json = is_json
    async def __aenter__(self):
      return self
    async def __aexit__(self, *args):
      pass
    async def json(self):
      return self.data
    async def text(self):
      if isinstance(self.data, bytes):
        return self.data.decode()
      return self.data
    async def read(self):
      if isinstance(self.data, str):
        return self.data.encode()
      return self.data

  class DummySession:
    async def __aenter__(self):
      return self
    async def __aexit__(self, *args):
      pass
    def get(self, url, headers=None):
      if url == "userinfo":
        return DummyResp(
          200,
          {"email": "user@example.com", "name": "User", "picture": "pic"},
          True,
        )
      if url == "pic":
        return DummyResp(200, b"imgbytes")
      return DummyResp(404, "", True)

  monkeypatch.setattr(
    google_provider, "aiohttp", types.SimpleNamespace(ClientSession=lambda: DummySession())
  )

  profile = asyncio.run(provider.fetch_user_profile("token"))
  expected = base64.b64encode(b"imgbytes").decode("utf-8")
  assert profile["profilePicture"] == expected
