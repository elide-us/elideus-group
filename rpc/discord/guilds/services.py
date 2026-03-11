from fastapi import Request
import logging

from queryregistry.discord.guilds import (
  get_guild_request,
  list_guilds_request,
  upsert_guild_request,
  update_credits_request,
)
from queryregistry.discord.guilds.models import (
  GuildIdParams,
  ListGuildsParams,
  UpsertGuildParams,
  UpdateGuildCreditsParams,
)
from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.db_module import DbModule

from .models import (
  DiscordGuildsGuildItem1,
  DiscordGuildsList1,
  DiscordGuildsSyncResult1,
  DiscordGuildsUpdateCredits1,
)


async def discord_guilds_list_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  db: DbModule = request.app.state.db
  await db.on_ready()
  res = await db.run(list_guilds_request(ListGuildsParams(include_inactive=True)))
  guilds = []
  for row in res.rows or []:
    guilds.append(DiscordGuildsGuildItem1(
      recid=row.get("recid", 0),
      guild_id=row.get("element_guild_id", ""),
      name=row.get("element_name", ""),
      joined_on=row.get("element_joined_on"),
      member_count=row.get("element_member_count"),
      owner_id=row.get("element_owner_id"),
      region=row.get("element_region"),
      left_on=row.get("element_left_on"),
      notes=row.get("element_notes"),
      credits=int(row.get("element_credits", 0) or 0),
    ))
  payload = DiscordGuildsList1(guilds=guilds)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def discord_guilds_get_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload_dict = rpc_request.payload or {}
  guild_id = payload_dict.get("guild_id", "")
  db: DbModule = request.app.state.db
  await db.on_ready()
  res = await db.run(get_guild_request(GuildIdParams(guild_id=guild_id)))
  row = res.rows[0] if res.rows else {}
  guild = DiscordGuildsGuildItem1(
    recid=row.get("recid", 0),
    guild_id=row.get("element_guild_id", guild_id),
    name=row.get("element_name", ""),
    joined_on=row.get("element_joined_on"),
    member_count=row.get("element_member_count"),
    owner_id=row.get("element_owner_id"),
    region=row.get("element_region"),
    left_on=row.get("element_left_on"),
    notes=row.get("element_notes"),
    credits=int(row.get("element_credits", 0) or 0),
  )
  return RPCResponse(op=rpc_request.op, payload=guild.model_dump(), version=rpc_request.version)


async def discord_guilds_update_credits_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = DiscordGuildsUpdateCredits1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()
  await db.run(update_credits_request(UpdateGuildCreditsParams(
    guild_id=payload.guild_id,
    credits=payload.credits,
  )))
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def discord_guilds_sync_v1(request: Request):
  """Sync live Discord bot guilds into the database.

  Reads bot.guilds from the running Discord bot, upserts each guild
  into the database, then returns the full updated guild list.
  """
  rpc_request, _, _ = await unbox_request(request)

  discord_bot = getattr(request.app.state, "discord_bot", None)
  if not discord_bot or not discord_bot.bot:
    logging.warning("[discord_guilds_sync_v1] Discord bot not available")
    return RPCResponse(
      op=rpc_request.op,
      payload=DiscordGuildsSyncResult1(synced=0, guilds=[]).model_dump(),
      version=rpc_request.version,
    )

  bot = discord_bot.bot
  db: DbModule = request.app.state.db
  await db.on_ready()

  synced = 0
  for guild in bot.guilds:
    try:
      await db.run(upsert_guild_request(UpsertGuildParams(
        guild_id=str(guild.id),
        name=guild.name,
        member_count=guild.member_count,
        owner_id=str(guild.owner_id) if guild.owner_id else None,
      )))
      synced += 1
    except Exception:
      logging.exception(
        "[discord_guilds_sync_v1] failed to upsert guild",
        extra={"guild_id": guild.id, "guild_name": guild.name},
      )

  res = await db.run(list_guilds_request(ListGuildsParams(include_inactive=True)))
  guilds = []
  for row in res.rows or []:
    guilds.append(DiscordGuildsGuildItem1(
      recid=row.get("recid", 0),
      guild_id=row.get("element_guild_id", ""),
      name=row.get("element_name", ""),
      joined_on=row.get("element_joined_on"),
      member_count=row.get("element_member_count"),
      owner_id=row.get("element_owner_id"),
      region=row.get("element_region"),
      left_on=row.get("element_left_on"),
      notes=row.get("element_notes"),
      credits=int(row.get("element_credits", 0) or 0),
    ))

  logging.info("[discord_guilds_sync_v1] synced %d guilds", synced)
  payload = DiscordGuildsSyncResult1(synced=synced, guilds=guilds)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )
