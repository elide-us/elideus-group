import logging
import uuid

from fastapi import HTTPException, Request

from queryregistry.discord.guilds import get_guild_request
from queryregistry.discord.guilds.models import GuildIdParams
from queryregistry.finance.credits import get_credits_request, set_credits_request
from queryregistry.finance.credits.models import GetCreditsParams, SetCreditsParams
from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.auth_module import AuthModule
from server.modules.oauth_module import OauthModule

from .models import (
  DiscordCommandGetCreditsRequest1,
  DiscordCommandGetCreditsResponse1,
  DiscordCommandGetGuildCreditsRequest1,
  DiscordCommandGetGuildCreditsResponse1,
  DiscordCommandGetRolesResponse1,
  DiscordCommandRegisterRequest1,
  DiscordCommandRegisterResponse1,
)


async def discord_command_get_roles_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = DiscordCommandGetRolesResponse1(roles=auth_ctx.roles)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def discord_command_register_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = DiscordCommandRegisterRequest1.model_validate(rpc_request.payload or {})
  discord_id = payload.discord_id
  auth: AuthModule = request.app.state.auth
  await auth.on_ready()
  guid, _, _ = await auth.get_discord_user_security(discord_id)
  if guid:
    response = DiscordCommandRegisterResponse1(
      success=True,
      message="You are already registered.",
      user_guid=guid,
    )
    return RPCResponse(op=rpc_request.op, payload=response.model_dump(), version=rpc_request.version)

  oauth: OauthModule = request.app.state.oauth
  await oauth.on_ready()
  provider_identifier = str(uuid.uuid5(uuid.NAMESPACE_URL, f"discord:{discord_id}"))
  discord_module = getattr(request.app.state, "discord_bot", None) or getattr(request.app.state, "discord", None)
  bot = getattr(discord_module, "bot", None)
  try:
    if bot is None:
      raise RuntimeError("Discord bot is unavailable")
    user = await bot.fetch_user(int(discord_id))
    display_name = user.display_name or str(discord_id)
  except Exception:
    logging.exception("[discord_command_register_v1] failed to fetch discord profile", extra={"discord_id": discord_id})
    display_name = str(discord_id)

  created = await oauth.create_user_from_provider(
    provider="discord",
    provider_identifier=provider_identifier,
    provider_email=f"{discord_id}@discord.placeholder",
    provider_displayname=display_name,
  )
  if not created or not created.get("guid"):
    raise HTTPException(status_code=500, detail="Unable to create user")

  new_user_guid = created["guid"]
  db = request.app.state.db
  await db.on_ready()
  await db.run(set_credits_request(SetCreditsParams(guid=new_user_guid, credits=50)))

  response = DiscordCommandRegisterResponse1(
    success=True,
    message="Registration complete. You have been granted 50 credits.",
    user_guid=new_user_guid,
    credits=50,
  )
  logging.info("[discord_command_register_v1] registered discord user", extra={"discord_id": discord_id, "user_guid": new_user_guid})
  return RPCResponse(op=rpc_request.op, payload=response.model_dump(), version=rpc_request.version)


async def discord_command_get_credits_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  DiscordCommandGetCreditsRequest1.model_validate(rpc_request.payload or {})
  if not auth_ctx.user_guid:
    raise HTTPException(status_code=403, detail="Registration required")

  db = request.app.state.db
  await db.on_ready()
  res = await db.run(get_credits_request(GetCreditsParams(guid=auth_ctx.user_guid)))
  row = res.rows[0] if res.rows else {}
  response = DiscordCommandGetCreditsResponse1(
    credits=int(row.get("element_credits", 0) or 0),
    reserve=row.get("element_reserve"),
  )
  logging.info("[discord_command_get_credits_v1] fetched credits", extra={"user_guid": auth_ctx.user_guid})
  return RPCResponse(op=rpc_request.op, payload=response.model_dump(), version=rpc_request.version)


async def discord_command_get_guild_credits_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = DiscordCommandGetGuildCreditsRequest1.model_validate(rpc_request.payload or {})

  db = request.app.state.db
  await db.on_ready()
  res = await db.run(get_guild_request(GuildIdParams(guild_id=payload.guild_id)))
  row = res.rows[0] if res.rows else {}
  response = DiscordCommandGetGuildCreditsResponse1(
    guild_id=payload.guild_id,
    credits=int(row.get("element_credits", 0) or 0),
  )
  logging.info("[discord_command_get_guild_credits_v1] fetched guild credits", extra={"guild_id": payload.guild_id})
  return RPCResponse(op=rpc_request.op, payload=response.model_dump(), version=rpc_request.version)
