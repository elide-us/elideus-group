from .services import discord_command_text_uwu_v1

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("text_uwu", "1"): discord_command_text_uwu_v1,
}

