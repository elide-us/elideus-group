from .services import (
    refresh_v1,
    invalidate_v1
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("refresh", "1"): refresh_v1,
  ("invalidate", "1"): invalidate_v1,
}
