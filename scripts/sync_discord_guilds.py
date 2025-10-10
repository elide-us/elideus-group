"""Console utility to synchronise Discord guilds with the database."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime

import discord
from fastapi import FastAPI

from server.helpers.logging import configure_root_logging
from server.modules.db_module import DbModule
from server.modules.env_module import EnvModule
from server.registry import RegistryDispatcher
from server.registry.system.discord.guilds import upsert_guild_request


LOGGER = logging.getLogger("scripts.sync_discord_guilds")


@dataclass(slots=True)
class SyncSummary:
  processed: int = 0
  skipped: int = 0
  duplicates: int = 0


def _extract_joined_on(guild: discord.Guild) -> datetime | None:
  member = getattr(guild, "me", None)
  joined = getattr(member, "joined_at", None) if member else None
  if joined is None:
    joined = getattr(guild, "joined_at", None)
  return joined


def _extract_region(guild: discord.Guild) -> str | None:
  region = getattr(guild, "preferred_locale", None) or getattr(guild, "region", None)
  if region is None:
    return None
  if isinstance(region, str):
    return region
  return str(region)


async def synchronize_guilds(client: discord.Client, db_module: DbModule, *, logger: logging.Logger | None = LOGGER) -> SyncSummary:
  summary = SyncSummary()
  seen_ids: set[str] = set()
  guilds = list(getattr(client, "guilds", []) or [])
  if logger:
    logger.info("Synchronising %d guilds", len(guilds))
  for guild in guilds:
    guild_id = getattr(guild, "id", None)
    if guild_id is None:
      summary.skipped += 1
      if logger:
        logger.warning("Skipping guild without identifier: %s", getattr(guild, "name", "<unknown>"))
      continue
    guild_key = str(guild_id)
    if guild_key in seen_ids:
      summary.duplicates += 1
      if logger:
        logger.info("Duplicate guild entry ignored: %s (%s)", getattr(guild, "name", guild_key), guild_key)
      continue
    seen_ids.add(guild_key)
    request = upsert_guild_request(
      guild_id=guild_key,
      name=getattr(guild, "name", guild_key),
      joined_on=_extract_joined_on(guild),
      member_count=getattr(guild, "member_count", None),
      owner_id=getattr(guild, "owner_id", None),
      region=_extract_region(guild),
    )
    await db_module.run(request)
    summary.processed += 1
    if logger:
      logger.info("Upserted guild %s (%s)", getattr(guild, "name", guild_key), guild_key)
  return summary


def _build_discord_client() -> discord.Client:
  intents = discord.Intents.default()
  intents.guilds = True
  intents.members = True
  intents.message_content = False
  return discord.Client(intents=intents)


async def _initialise_modules() -> tuple[FastAPI, EnvModule, DbModule, RegistryDispatcher]:
  app = FastAPI()
  registry = RegistryDispatcher()
  env_module = EnvModule(app)
  db_module = DbModule(app)
  app.state.registry = registry
  app.state.env = env_module
  db_module.set_registry(registry)
  app.state.db = db_module
  await env_module.startup()
  await db_module.startup()
  return app, env_module, db_module, registry


async def _shutdown_modules(env_module: EnvModule, db_module: DbModule) -> None:
  with suppress(Exception):
    await db_module.shutdown()
  with suppress(Exception):
    await env_module.shutdown()


async def run() -> SyncSummary:
  configure_root_logging()
  LOGGER.info("Starting Discord guild synchronisation utility")
  summary = SyncSummary()
  try:
    _, env_module, db_module, _ = await _initialise_modules()
  except Exception:
    LOGGER.exception("Failed to initialise environment or database modules")
    raise
  token = env_module.get("DISCORD_SECRET")
  client = _build_discord_client()
  ready_event = asyncio.Event()

  @client.event
  async def on_ready():
    LOGGER.info("Discord client ready: %s", client.user)
    ready_event.set()

  connect_task = asyncio.create_task(client.start(token))
  ready_task = asyncio.create_task(ready_event.wait())
  try:
    done, pending = await asyncio.wait({ready_task, connect_task}, return_when=asyncio.FIRST_COMPLETED)
    if ready_task in done:
      summary = await synchronize_guilds(client, db_module, logger=LOGGER)
    else:
      # Connection failed before the client became ready.
      if connect_task in done:
        exc = connect_task.exception()
        if exc:
          raise exc
  finally:
    ready_task.cancel()
    await client.close()
    with suppress(asyncio.CancelledError):
      await connect_task
    await _shutdown_modules(env_module, db_module)
  LOGGER.info(
    "Synchronization complete. processed=%d skipped=%d duplicates=%d",
    summary.processed,
    summary.skipped,
    summary.duplicates,
  )
  return summary


def main() -> None:
  asyncio.run(run())


if __name__ == "__main__":
  main()

