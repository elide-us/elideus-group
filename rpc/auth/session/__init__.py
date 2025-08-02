from .services import (auth_session_get_token_v1,
                       auth_session_refresh_token_v1,
                       auth_session_invalidate_token_v1)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_token", "1"): auth_session_get_token_v1,
  ("refresh_token", "1"): auth_session_refresh_token_v1,
  ("invalidate_token", "1"): auth_session_invalidate_token_v1,
}

