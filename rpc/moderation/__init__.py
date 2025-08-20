"""Moderation namespace for reviewing user content.

Requires ROLE_MODERATOR.
"""

from .content.handler import handle_content_request

HANDLERS: dict[str, callable] = {
  "content": handle_content_request,
}
