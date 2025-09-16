"""Discord RPC namespace.

Provides handlers for Discord bot operations (``ROLE_DISCORD_BOT``) and Discord
administration flows (``ROLE_DISCORD_ADMIN``).
"""

from .bsky.handler import handle_bsky_request
from .chat.handler import handle_chat_request
from .command.handler import handle_command_request
from .ongoing.handler import handle_ongoing_request
from .personas.handler import handle_personas_request

HANDLERS: dict[str, callable] = {
  "bsky": handle_bsky_request,
  "chat": handle_chat_request,
  "command": handle_command_request,
  "ongoing": handle_ongoing_request,
  "personas": handle_personas_request,
}


REQUIRED_ROLES: dict[str, str] = {
  "bsky": "ROLE_DISCORD_BOT",
  "chat": "ROLE_DISCORD_BOT",
  "command": "ROLE_DISCORD_BOT",
  "ongoing": "ROLE_DISCORD_BOT",
  "personas": "ROLE_DISCORD_ADMIN",
}


FORBIDDEN_DETAILS: dict[str, str] = {
  "bsky": 'You must have the Discord bot role assigned to use this bot.',
  "chat": 'You must have the Discord bot role assigned to use this bot.',
  "command": 'You must have the Discord bot role assigned to use this bot.',
  "ongoing": 'You must have the Discord bot role assigned to use this bot.',
  "personas": 'Forbidden',
}
