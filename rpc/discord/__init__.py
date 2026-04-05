"""Discord RPC namespace.

Provides handlers for Discord RPC operations gated at the domain level.
"""

from .bsky.handler import handle_bsky_request
from .chat.handler import handle_chat_request
from .command.handler import handle_command_request

HANDLERS: dict[str, callable] = {
  "bsky": handle_bsky_request,
  "chat": handle_chat_request,
  "command": handle_command_request,
}
