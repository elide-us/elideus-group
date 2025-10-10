"""Tests for the Discord guild synchronisation utility."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace

from scripts.sync_discord_guilds import SyncSummary, synchronize_guilds
from server.modules.providers import DBResult
from server.registry.types import DBRequest


@dataclass
class _CapturedRequest:
  request: DBRequest


class _StubDbModule:
  def __init__(self):
    self.requests: list[_CapturedRequest] = []

  async def run(self, request: DBRequest):
    self.requests.append(_CapturedRequest(request))
    return DBResult(rows=[{"recid": len(self.requests)}], rowcount=1)


class _StubGuild:
  def __init__(
    self,
    *,
    guild_id: int | str | None,
    name: str = "Guild",
    joined_at: datetime | None = None,
    member_count: int | None = None,
    owner_id: int | str | None = None,
    region: str | None = None,
  ):
    self.id = guild_id
    self.name = name
    self.joined_at = joined_at
    self.member_count = member_count
    self.owner_id = owner_id
    self.region = region
    self.preferred_locale = None
    if joined_at is not None:
      self.me = SimpleNamespace(joined_at=joined_at)
    else:
      self.me = SimpleNamespace(joined_at=None)


class _StubClient:
  def __init__(self, guilds: list[_StubGuild]):
    self.guilds = guilds


def _run(coro):
  return asyncio.run(coro)


def test_synchronize_guilds_upserts_each_guild():
  joined = datetime(2024, 1, 2, tzinfo=timezone.utc)
  guilds = [
    _StubGuild(guild_id=1, name="Alpha", joined_at=joined, member_count=5, owner_id=42, region="us"),
    _StubGuild(guild_id="2", name="Beta", joined_at=None, member_count=10, owner_id="99"),
  ]
  client = _StubClient(guilds)
  db = _StubDbModule()

  summary = _run(synchronize_guilds(client, db, logger=None))

  assert summary == SyncSummary(processed=2, skipped=0, duplicates=0)
  assert len(db.requests) == 2
  first = db.requests[0].request
  assert first.op == "db:system:discord_guilds:upsert_guild:1"
  assert first.params["guild_id"] == "1"
  assert first.params["name"] == "Alpha"
  assert first.params["joined_on"] == joined.isoformat()
  assert first.params["member_count"] == 5
  assert first.params["owner_id"] == "42"
  assert first.params["region"] == "us"


def test_synchronize_guilds_skips_duplicate_ids():
  joined = datetime(2024, 5, 6, tzinfo=timezone.utc)
  guilds = [
    _StubGuild(guild_id=123, name="Gamma", joined_at=joined),
    _StubGuild(guild_id=123, name="Gamma Clone", joined_at=joined),
  ]
  client = _StubClient(guilds)
  db = _StubDbModule()

  summary = _run(synchronize_guilds(client, db, logger=None))

  assert summary == SyncSummary(processed=1, skipped=0, duplicates=1)
  assert len(db.requests) == 1


def test_synchronize_guilds_skips_missing_identifier():
  guilds = [
    _StubGuild(guild_id=None, name="Nameless"),
  ]
  client = _StubClient(guilds)
  db = _StubDbModule()

  summary = _run(synchronize_guilds(client, db, logger=None))

  assert summary == SyncSummary(processed=0, skipped=1, duplicates=0)
  assert not db.requests

