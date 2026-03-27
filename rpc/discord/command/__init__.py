from .services import (
  discord_command_get_credits_v1,
  discord_command_get_guild_credits_v1,
  discord_command_get_roles_v1,
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_roles", "1"): discord_command_get_roles_v1,
  ("get_credits", "1"): discord_command_get_credits_v1,
  ("get_guild_credits", "1"): discord_command_get_guild_credits_v1,
}
