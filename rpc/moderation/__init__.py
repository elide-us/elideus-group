from .services import moderation_review_content_v1

DISPATCHERS: dict[tuple[str, str], callable] = {
  # Requires ROLE_MODERATOR.
  ("review_content", "1"): moderation_review_content_v1
}
