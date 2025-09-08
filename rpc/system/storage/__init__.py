from .services import (
  system_storage_get_stats_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_stats", "1"): system_storage_get_stats_v1,
}

