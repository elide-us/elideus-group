"""Discord namespace for bot interactions.

Requires ROLE_DISCORD_BOT.
"""

from .chat.handler import handle_chat_request
from .command.handler import handle_command_request

HANDLERS: dict[str, callable] = {
  "chat": handle_chat_request,
  "command": handle_command_request,
}
