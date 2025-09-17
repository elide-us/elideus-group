from .services import discord_command_get_roles_v1

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_roles", "1"): discord_command_get_roles_v1,
}

