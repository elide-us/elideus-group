"""Standalone utility to pull Discord guilds and insert them into SQL Server.

This script deliberately avoids any of the application server modules. It
implements a tiny asynchronous connection pool on top of ``aioodbc`` and uses
raw SQL statements to upsert guild metadata into the ``discord_guilds`` table.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Sequence

import aioodbc
import discord
from dotenv import load_dotenv


LOGGER = logging.getLogger("scripts.direct_insert_discord_guilds")


class ConnectionPool:
  """Very small async connection pool for aioodbc connections."""

  def __init__(
    self,
    dsn: str,
    *,
    max_size: int = 5,
    timeout: float | None = 30.0,
    autocommit: bool = True,
  ) -> None:
    if max_size <= 0:
      raise ValueError("max_size must be positive")
    self._dsn = dsn
    self._max_size = max_size
    self._timeout = timeout
    self._autocommit = autocommit
    self._available: asyncio.LifoQueue[aioodbc.Connection] = asyncio.LifoQueue(max_size)
    self._created = 0
    self._lock = asyncio.Lock()
    self._closed = False
    self._in_use: set[aioodbc.Connection] = set()

  async def _create(self) -> aioodbc.Connection:
    conn = await aioodbc.connect(dsn=self._dsn, autocommit=self._autocommit)
    self._created += 1
    return conn

  async def _get_from_queue(self) -> aioodbc.Connection:
    if self._timeout is None:
      return await self._available.get()
    return await asyncio.wait_for(self._available.get(), timeout=self._timeout)

  async def _finalize(self, conn: aioodbc.Connection) -> None:
    with suppress(Exception):
      await conn.close()
    if self._created:
      self._created -= 1

  @asynccontextmanager
  async def connection(self) -> aioodbc.Connection:
    conn = await self.acquire()
    try:
      yield conn
    finally:
      await self.release(conn)

  async def acquire(self) -> aioodbc.Connection:
    if self._closed:
      raise RuntimeError("Connection pool is closed")
    while True:
      try:
        conn = self._available.get_nowait()
      except asyncio.QueueEmpty:
        async with self._lock:
          if self._closed:
            raise RuntimeError("Connection pool is closed")
          if self._created < self._max_size:
            conn = await self._create()
            break
        conn = await self._get_from_queue()
      if getattr(conn, "closed", False):
        await self._finalize(conn)
        continue
      break
    self._in_use.add(conn)
    return conn

  async def release(self, conn: aioodbc.Connection) -> None:
    if conn not in self._in_use:
      return
    self._in_use.discard(conn)
    if self._closed or getattr(conn, "closed", False):
      await self._finalize(conn)
      return
    try:
      self._available.put_nowait(conn)
    except asyncio.QueueFull:
      await self._finalize(conn)

  async def close(self) -> None:
    if self._closed:
      return
    self._closed = True
    while not self._available.empty():
      conn = await self._available.get()
      await self._finalize(conn)
    for conn in list(self._in_use):
      with suppress(Exception):
        await conn.close()
    self._in_use.clear()


@dataclass(slots=True)
class GuildRecord:
  guild_id: str
  name: str
  joined_on: datetime | None
  member_count: int | None
  owner_id: str | None
  region: str | None


UPSERT_SQL = """
DECLARE @result TABLE (
  recid BIGINT,
  element_guild_id NVARCHAR(64),
  element_name NVARCHAR(512),
  element_joined_on DATETIME2(7),
  element_member_count INT,
  element_owner_id NVARCHAR(64),
  element_region NVARCHAR(256),
  element_left_on DATETIME2(7),
  element_notes NVARCHAR(MAX)
);

UPDATE discord_guilds
  SET
    element_name = ?,
    element_member_count = ?,
    element_owner_id = ?,
    element_region = ?,
    element_left_on = ?,
    element_notes = ?,
    element_joined_on = COALESCE(?, element_joined_on)
  OUTPUT
    inserted.recid,
    inserted.element_guild_id,
    inserted.element_name,
    inserted.element_joined_on,
    inserted.element_member_count,
    inserted.element_owner_id,
    inserted.element_region,
    inserted.element_left_on,
    inserted.element_notes
  INTO @result
  WHERE element_guild_id = ?;

IF @@ROWCOUNT = 0
BEGIN
  INSERT INTO discord_guilds (
    element_guild_id,
    element_name,
    element_joined_on,
    element_member_count,
    element_owner_id,
    element_region,
    element_left_on,
    element_notes
  )
  OUTPUT
    inserted.recid,
    inserted.element_guild_id,
    inserted.element_name,
    inserted.element_joined_on,
    inserted.element_member_count,
    inserted.element_owner_id,
    inserted.element_region,
    inserted.element_left_on,
    inserted.element_notes
  INTO @result
  VALUES (
    ?,
    ?,
    COALESCE(?, SYSUTCDATETIME()),
    ?,
    ?,
    ?,
    ?,
    ?
  );
END;

SELECT
  recid,
  element_guild_id,
  element_name,
  element_joined_on,
  element_member_count,
  element_owner_id,
  element_region,
  element_left_on,
  element_notes
FROM @result;
"""


def _normalise_joined_on(joined: datetime | None) -> datetime | None:
  if joined is None:
    return None
  if joined.tzinfo is not None:
    joined = joined.astimezone(timezone.utc).replace(tzinfo=None)
  return joined


def _extract_region(guild: discord.Guild) -> str | None:
  region = getattr(guild, "preferred_locale", None) or getattr(guild, "region", None)
  if region is None:
    return None
  return str(region)


def build_guild_records(guilds: Sequence[discord.Guild]) -> list[GuildRecord]:
  records: list[GuildRecord] = []
  for guild in guilds:
    guild_id = getattr(guild, "id", None)
    if guild_id is None:
      LOGGER.warning("Skipping guild without identifier: %s", getattr(guild, "name", "<unknown>"))
      continue
    member = getattr(guild, "me", None)
    joined = getattr(member, "joined_at", None) if member else None
    if joined is None:
      joined = getattr(guild, "joined_at", None)
    record = GuildRecord(
      guild_id=str(guild_id),
      name=getattr(guild, "name", str(guild_id)),
      joined_on=_normalise_joined_on(joined),
      member_count=getattr(guild, "member_count", None),
      owner_id=str(getattr(guild, "owner_id", "")) if getattr(guild, "owner_id", None) is not None else None,
      region=_extract_region(guild),
    )
    records.append(record)
  return records


async def fetch_guilds(token: str) -> list[discord.Guild]:
  intents = discord.Intents.default()
  intents.guilds = True
  intents.members = True
  client = discord.Client(intents=intents)
  ready = asyncio.Event()

  @client.event
  async def on_ready() -> None:
    LOGGER.info("Discord client connected as %s", client.user)
    ready.set()

  connect_task = asyncio.create_task(client.start(token))
  try:
    await ready.wait()
    guilds = list(client.guilds)
  finally:
    await client.close()
    with suppress(asyncio.CancelledError):
      await connect_task
  return guilds


async def upsert_guilds(pool: ConnectionPool, records: Iterable[GuildRecord]) -> int:
  processed = 0
  async with pool.connection() as conn:
    async with conn.cursor() as cursor:
      for record in records:
        params = (
          record.name,
          record.member_count,
          record.owner_id,
          record.region,
          None,
          None,
          record.joined_on,
          record.guild_id,
          record.guild_id,
          record.name,
          record.joined_on,
          record.member_count,
          record.owner_id,
          record.region,
          None,
          None,
        )
        await cursor.execute(UPSERT_SQL, params)
        await cursor.fetchall()
        processed += 1
  return processed


def _configure_logging(level: str) -> None:
  logging.basicConfig(
    level=getattr(logging, level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
  )


def _parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Insert Discord guild metadata directly into SQL Server")
  parser.add_argument("--max-pool-size", type=int, default=5, help="Maximum number of pooled SQL connections")
  parser.add_argument("--timeout", type=float, default=30.0, help="Seconds to wait for a pooled connection")
  parser.add_argument("--log-level", default="INFO", help="Logging level (default: INFO)")
  return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
  load_dotenv()
  _configure_logging(args.log_level)

  token = os.environ.get("DISCORD_SECRET")
  if not token:
    raise RuntimeError("DISCORD_SECRET environment variable is required")
  dsn = os.environ.get("AZURE_SQL_CONNECTION_STRING")
  if not dsn:
    raise RuntimeError("AZURE_SQL_CONNECTION_STRING environment variable is required")

  pool = ConnectionPool(dsn, max_size=args.max_pool_size, timeout=args.timeout)
  try:
    guilds = await fetch_guilds(token)
    records = build_guild_records(guilds)
    if not records:
      LOGGER.info("No guilds available to insert")
      return
    processed = await upsert_guilds(pool, records)
    LOGGER.info("Completed guild synchronisation: processed=%d", processed)
  finally:
    await pool.close()


def main() -> None:
  args = _parse_args()
  asyncio.run(run(args))


if __name__ == "__main__":
  main()
