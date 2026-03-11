from .services import (
  discord_guilds_get_v1,
  discord_guilds_list_v1,
  discord_guilds_sync_v1,
  discord_guilds_update_credits_v1,
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list_guilds", "1"): discord_guilds_list_v1,
  ("get_guild", "1"): discord_guilds_get_v1,
  ("update_credits", "1"): discord_guilds_update_credits_v1,
  ("sync_guilds", "1"): discord_guilds_sync_v1,
}
