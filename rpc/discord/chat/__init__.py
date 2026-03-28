from .services import (
  discord_chat_deliver_persona_response_v1,
  discord_chat_get_channel_history_v1,
  discord_chat_persona_command_v1,
  discord_chat_persona_response_v1,
  discord_chat_summarize_channel_v1,
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("persona_command", "1"): discord_chat_persona_command_v1,
  ("persona_response", "1"): discord_chat_persona_response_v1,
  ("summarize_channel", "1"): discord_chat_summarize_channel_v1,
  ("get_channel_history", "1"): discord_chat_get_channel_history_v1,
  ("deliver_persona_response", "1"): discord_chat_deliver_persona_response_v1,
}
