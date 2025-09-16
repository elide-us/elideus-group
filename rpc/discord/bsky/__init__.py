from .services import discord_bsky_post_message_v1

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("post", "1"): discord_bsky_post_message_v1,
}
