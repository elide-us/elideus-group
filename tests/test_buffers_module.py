import pytest, asyncio
from server.helpers.buffers import AsyncBufferWriter
import server.helpers.buffers as buffers

class DummyResp:
  def __init__(self, data=b'data', status=200):
    self._data = data
    self.status = status
  def raise_for_status(self):
    if self.status >= 400:
      from aiohttp import ClientError
      raise ClientError("bad")
  async def read(self):
    return self._data
  async def __aenter__(self):
    return self
  async def __aexit__(self, *exc):
    return False

class DummySession:
  def __init__(self, resp):
    self.resp = resp
  def get(self, url):
    return self.resp
  async def __aenter__(self):
    return self
  async def __aexit__(self, *exc):
    return False

async def _use_buffer():
  async with AsyncBufferWriter('url') as buf:
    return buf.read()

async def _use_bytes():
  async with AsyncBufferWriter(b'data') as buf:
    return buf.read()


def test_buffer_success(monkeypatch):
  monkeypatch.setattr(buffers.aiohttp, 'ClientSession', lambda: DummySession(DummyResp()))
  data = asyncio.run(_use_buffer())
  assert data == b'data'


def test_buffer_error(monkeypatch):
  monkeypatch.setattr(buffers.aiohttp, 'ClientSession', lambda: DummySession(DummyResp(status=500)))
  with pytest.raises(ValueError):
    asyncio.run(_use_buffer())


def test_buffer_from_bytes():
  data = asyncio.run(_use_bytes())
  assert data == b'data'

