import asyncio

import pytest

from server.modules.providers.database.mssql_provider import logic


class DummyPool:
  def __init__(self):
    self.closed = False
    self.waited = False

  def close(self):
    self.closed = True

  async def wait_closed(self):
    self.waited = True


def _reset_pool_state(monkeypatch):
  monkeypatch.setattr(logic, "_pool", None)
  monkeypatch.setattr(logic, "_pool_config", None)
  monkeypatch.setattr(logic, "_init_lock", asyncio.Lock())


def test_init_pool_idempotent(monkeypatch):
  dummy_pool = DummyPool()
  created = 0

  async def fake_create_pool(**kwargs):
    nonlocal created
    created += 1
    await asyncio.sleep(0)
    return dummy_pool

  _reset_pool_state(monkeypatch)
  monkeypatch.setattr(logic.aioodbc, "create_pool", fake_create_pool)

  asyncio.run(logic.init_pool(dsn="dsn://test", minsize=1, maxsize=5))
  asyncio.run(logic.init_pool(dsn="dsn://test", minsize=1, maxsize=5))

  assert created == 1
  assert logic._pool is dummy_pool

  asyncio.run(logic.close_pool())
  assert dummy_pool.closed is True
  assert dummy_pool.waited is True


def test_init_pool_conflicting_configuration(monkeypatch):
  dummy_pool = DummyPool()

  async def fake_create_pool(**kwargs):
    return dummy_pool

  _reset_pool_state(monkeypatch)
  monkeypatch.setattr(logic.aioodbc, "create_pool", fake_create_pool)

  asyncio.run(logic.init_pool(dsn="dsn://test", minsize=1))

  with pytest.raises(RuntimeError):
    asyncio.run(logic.init_pool(dsn="dsn://test", minsize=2))

  asyncio.run(logic.close_pool())


def test_init_pool_concurrent_calls(monkeypatch):
  dummy_pool = DummyPool()
  created = 0

  async def fake_create_pool(**kwargs):
    nonlocal created
    created += 1
    await asyncio.sleep(0.01)
    return dummy_pool

  _reset_pool_state(monkeypatch)
  monkeypatch.setattr(logic.aioodbc, "create_pool", fake_create_pool)

  async def _runner():
    await asyncio.gather(*[
      logic.init_pool(dsn="dsn://test", minsize=1, maxsize=4)
      for _ in range(5)
    ])

  asyncio.run(_runner())

  assert created == 1
  assert logic._pool is dummy_pool

  asyncio.run(logic.close_pool())
