import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta

from types import SimpleNamespace
from fastapi import FastAPI

from server.modules.oauth_module import OauthModule


def test_extract_identifiers_bad_base(caplog):
  oauth = OauthModule(FastAPI())
  caplog.set_level(logging.ERROR)
  ids = oauth.extract_identifiers("not-a-uuid", {}, "microsoft")
  assert "not-a-uuid" in ids
  assert len(ids) == 1
  assert any("home_account_id generation failed" in r.message for r in caplog.records)


class DummyDb:
  def __init__(self):
    self.calls = []

  async def run(self, op, args):
    self.calls.append((op, args))
    if op == "db:auth:session:create_session:1":
      return SimpleNamespace(rows=[{"session_guid": "sess", "device_guid": "dev"}])
    if op == "db:auth:session:update_device_token:1":
      return SimpleNamespace(rows=[], rowcount=1)
    return SimpleNamespace(rows=[])


def test_lookup_user_skips_invalid_identifier():
  oauth = OauthModule(FastAPI())
  db = DummyDb()
  oauth.db = db
  user = asyncio.run(oauth.lookup_user("microsoft", ["bad-id"]))
  assert user is None
  assert db.calls == []


class DummyAuth:
  def make_rotation_token(self, guid):
    return "rot", datetime.now(timezone.utc) + timedelta(hours=1)

  def make_session_token(self, guid, rot, session_guid, device_guid, roles, exp=None):
    return "sess", exp or datetime.now(timezone.utc) + timedelta(hours=1)

  async def get_user_roles(self, guid, refresh=False):
    return [], 0


def test_create_session_handles_missing_roles():
  oauth = OauthModule(FastAPI())
  db = DummyDb()
  auth = DummyAuth()
  oauth.db = db
  oauth.auth = auth
  token, exp, rot, rot_exp = asyncio.run(
    oauth.create_session(str(uuid.uuid4()), "microsoft", "fp", None, None)
  )
  assert token == "sess"
  assert rot == "rot"
  ops = [op for op, _ in db.calls]
  assert "db:auth:session:create_session:1" in ops
  args = [a for op, a in db.calls if op == "db:auth:session:create_session:1"][0]
  assert args["provider"] == "microsoft"

