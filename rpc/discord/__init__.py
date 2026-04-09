"""Discord RPC namespace.

Provides handlers for Discord RPC operations gated at the domain level.
"""

from .chat.handler import handle_chat_request
from .command.handler import handle_command_request

HANDLERS: dict[str, callable] = {
  "chat": handle_chat_request,
  "command": handle_command_request,
}
