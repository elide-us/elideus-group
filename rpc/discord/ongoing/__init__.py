from .services import (
  discord_ongoing_countdown_v1,
  discord_ongoing_toggle_active_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("toggle_active", "1"): discord_ongoing_toggle_active_v1,
  ("countdown", "1"): discord_ongoing_countdown_v1,
}
