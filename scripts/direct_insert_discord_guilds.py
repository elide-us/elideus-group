"""Standalone utility to pull Discord guilds and dump the records to stdout.

This variant exists for manual workflows where inserting into SQL Server is
performed outside of the application runtime. It connects to Discord, gathers
metadata for each guild the bot can access, normalises it to match the
``discord_guilds`` schema, and prints the resulting payloads as JSON. The JSON
output can then be used to craft manual ``INSERT`` statements or seed files.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

import discord
from dotenv import load_dotenv


LOGGER = logging.getLogger("scripts.direct_insert_discord_guilds")


@dataclass(slots=True)
class GuildRecord:
  guild_id: str
  name: str
  joined_on: datetime | None
  member_count: int | None
  owner_id: str | None
  region: str | None


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


def _record_to_payload(record: GuildRecord) -> dict[str, object]:
  return {
    "element_guild_id": record.guild_id,
    "element_name": record.name,
    "element_joined_on": record.joined_on.isoformat(timespec="seconds") if record.joined_on else None,
    "element_member_count": record.member_count,
    "element_owner_id": record.owner_id,
    "element_region": record.region,
    "element_left_on": None,
    "element_notes": None,
  }


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


def _configure_logging(level: str) -> None:
  logging.basicConfig(
    level=getattr(logging, level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
  )


def _parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Dump Discord guild metadata for manual SQL insertion")
  parser.add_argument("--log-level", default="INFO", help="Logging level (default: INFO)")
  return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
  load_dotenv()
  _configure_logging(args.log_level)

  token = os.environ.get("DISCORD_SECRET")
  if not token:
    raise RuntimeError("DISCORD_SECRET environment variable is required")
  guilds = await fetch_guilds(token)
  records = build_guild_records(guilds)
  if not records:
    LOGGER.info("No guilds available to insert")
    return

  payloads = [_record_to_payload(record) for record in records]
  print(json.dumps(payloads, indent=2))
  LOGGER.info("Prepared %d guild record(s) for manual insertion", len(payloads))


def main() -> None:
  args = _parse_args()
  asyncio.run(run(args))


if __name__ == "__main__":
  main()
