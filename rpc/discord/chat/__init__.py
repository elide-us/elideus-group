from .services import (
  discord_chat_summarize_channel_v1,
  discord_chat_uwu_chat_v1,
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("summarize_channel", "1"): discord_chat_summarize_channel_v1,
  ("uwu_chat", "1"): discord_chat_uwu_chat_v1,
}
