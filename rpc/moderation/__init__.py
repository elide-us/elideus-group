"""Moderation namespace for reviewing user content.

Requires ROLE_MODERATION_SUPPORT.
"""

from .content.handler import handle_content_request

HANDLERS: dict[str, callable] = {
  "content": handle_content_request,
}
