"""Content moderation RPC namespace.

Requires ROLE_MODERATION_SUPPORT.
"""

from .services import (
  moderation_content_review_content_v1,
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("review_content", "1"): moderation_content_review_content_v1,
}
