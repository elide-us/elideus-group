import asyncio, logging, uuid
from types import SimpleNamespace
from datetime import datetime, timezone, timedelta

import pytest

from rpc.auth.microsoft.services import extract_identifiers, lookup_user, create_session


def test_extract_identifiers_bad_base(caplog):
  caplog.set_level(logging.ERROR)
  ids = extract_identifiers("not-a-uuid", {})
  assert "not-a-uuid" in ids
  assert len(ids) == 1
  assert any("home_account_id generation failed" in r.message for r in caplog.records)


class DummyDb:
  def __init__(self):
    self.calls = []
  async def run(self, op, args):
    self.calls.append((op, args))
    return SimpleNamespace(rows=[])


def test_lookup_user_skips_invalid_identifier():
  db = DummyDb()
  user = asyncio.run(lookup_user(db, "microsoft", ["bad-id"]))
  assert user is None
  assert db.calls == []


class DummyAuth:
  def make_rotation_token(self, guid):
    return "rot", datetime.now(timezone.utc) + timedelta(hours=1)
  def make_session_token(self, guid, rot, roles, provider):
    return "sess", datetime.now(timezone.utc) + timedelta(hours=1)
  async def get_user_roles(self, guid, refresh=False):
    return [], 0


def test_create_session_handles_missing_roles():
  db = DummyDb()
  auth = DummyAuth()
  token, exp = asyncio.run(
    create_session(auth, db, str(uuid.uuid4()), "microsoft", None, None, None)
  )
  assert token == "sess"
  ops = [op for op, _ in db.calls]
  assert "db:auth:session:create_session:1" in ops

