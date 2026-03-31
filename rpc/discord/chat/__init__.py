from .services import (
  discord_chat_persona_response_v1,
  discord_chat_summarize_channel_v1,
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("persona_response", "1"): discord_chat_persona_response_v1,
  ("summarize_channel", "1"): discord_chat_summarize_channel_v1,
}
