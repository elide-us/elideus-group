import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from server.registry.users.security.sessions import mssql as security_sessions


def test_create_session_updates_existing(monkeypatch):
  executed: list[str] = []
  lookups: list[tuple[str, bool]] = []

  class DummyCur:
    def __init__(self):
      self._step = 0
    async def execute(self, sql, params):
      executed.append(sql.lower())
    async def fetchone(self):
      if self._step == 0:
        self._step += 1
        return ("sess",)
      if self._step == 1:
        self._step += 1
        return ("dev",)
      return None

  @asynccontextmanager
  async def fake_tx():
    yield DummyCur()

  async def fake_lookup(provider, *, cursor=None):
    lookups.append((provider, cursor is not None))
    return 1

  monkeypatch.setattr(security_sessions, "transaction", fake_tx)
  monkeypatch.setattr(security_sessions, "get_auth_provider_recid", fake_lookup)

  args = {
    "access_token": "tok",
    "expires": datetime.now(timezone.utc),
    "fingerprint": "fp",
    "user_agent": None,
    "ip_address": None,
    "user_guid": "user",
    "provider": "microsoft",
  }

  asyncio.run(security_sessions.create_session_v1(args))

  assert any("update users_sessions" in q for q in executed)
  assert not any("insert into users_sessions" in q for q in executed)
  assert any("update sessions_devices" in q for q in executed)
  assert not any("insert into sessions_devices" in q for q in executed)
  assert lookups == [("microsoft", True)]
