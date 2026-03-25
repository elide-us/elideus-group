from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  DiscordGuildsGuildItem1,
  DiscordGuildsList1,
  DiscordGuildsSyncResult1,
  DiscordGuildsUpdateCredits1,
)


async def discord_guilds_list_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  module = getattr(request.app.state, "discord_bot", None) or getattr(request.app.state, "discord", None)
  await module.on_ready()
  guilds = await module.list_guild_records()
  payload = DiscordGuildsList1(guilds=[DiscordGuildsGuildItem1(**row) for row in guilds])
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def discord_guilds_get_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload_dict = rpc_request.payload or {}
  guild_id = payload_dict.get("guild_id", "")
  module = getattr(request.app.state, "discord_bot", None) or getattr(request.app.state, "discord", None)
  await module.on_ready()
  guild = await module.get_guild_record(guild_id)
  response = DiscordGuildsGuildItem1(**guild)
  return RPCResponse(op=rpc_request.op, payload=response.model_dump(), version=rpc_request.version)


async def discord_guilds_update_credits_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = DiscordGuildsUpdateCredits1(**(rpc_request.payload or {}))
  module = getattr(request.app.state, "discord_bot", None) or getattr(request.app.state, "discord", None)
  await module.on_ready()
  result = await module.update_guild_credits(payload.guild_id, payload.credits)
  response = DiscordGuildsUpdateCredits1(**result)
  return RPCResponse(op=rpc_request.op, payload=response.model_dump(), version=rpc_request.version)


async def discord_guilds_sync_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  module = getattr(request.app.state, "discord_bot", None) or getattr(request.app.state, "discord", None)
  await module.on_ready()
  synced = await module.sync_guild_records()
  payload = DiscordGuildsSyncResult1(
    synced=synced.get("synced", 0),
    guilds=[DiscordGuildsGuildItem1(**row) for row in synced.get("guilds", [])],
  )
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
