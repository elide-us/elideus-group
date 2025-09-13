import asyncio
import base64
import types
import uuid

from server.modules.providers.auth import discord_provider


def test_verify_id_token(monkeypatch):
  provider = discord_provider.DiscordAuthProvider()

  class DummyResp:
    def __init__(self, status, data):
      self.status = status
      self.data = data
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
      assert headers["Authorization"] == "Bearer token"
      return DummyResp(200, {"id": "123"})

  monkeypatch.setattr(
    discord_provider,
    "aiohttp",
    types.SimpleNamespace(ClientSession=lambda: DummySession()),
  )

  payload = asyncio.run(provider.verify_id_token("token"))
  assert payload["id"] == "123"


def test_fetch_user_profile_downloads_avatar(monkeypatch):
  provider = discord_provider.DiscordAuthProvider()

  avatar_bytes = b"avatar"

  class DummyResp:
    def __init__(self, status, data):
      self.status = status
      self.data = data
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
      if url == discord_provider.USERINFO_URL:
        return DummyResp(
          200,
          {
            "id": "123",
            "email": "user@example.com",
            "username": "User",
            "avatar": "hash",
          },
        )
      if url == "https://cdn.discordapp.com/avatars/123/hash.png":
        return DummyResp(200, avatar_bytes)
      return DummyResp(404, "")

  monkeypatch.setattr(
    discord_provider,
    "aiohttp",
    types.SimpleNamespace(ClientSession=lambda: DummySession()),
  )

  profile = asyncio.run(provider.fetch_user_profile("token"))
  expected = base64.b64encode(avatar_bytes).decode("utf-8")
  assert profile["profilePicture"] == expected
  assert profile["email"] == "user@example.com"
  assert profile["username"] == "User"


def test_extract_guid():
  provider = discord_provider.DiscordAuthProvider()
  payload = {"id": "42"}
  expected = str(uuid.uuid5(uuid.NAMESPACE_URL, "discord:42"))
  assert provider.extract_guid(payload) == expected


def test_requires_id_token_is_false():
  provider = discord_provider.DiscordAuthProvider()
  assert provider.requires_id_token is False
