"""Discord namespace for bot interactions.

Requires ROLE_DISCORD_BOT.
"""

from .command.handler import handle_command_request

HANDLERS: dict[str, callable] = {
  "command": handle_command_request,
}
