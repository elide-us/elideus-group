from .services import (
    get_home_v1,
    get_routes_v1
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_home", "1"): get_home_v1,
  ("get_routes", "1"): get_routes_v1,
}
