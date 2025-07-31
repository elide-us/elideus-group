from . import services

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_home", "1"): services.get_home_v1,
  ("get_routes", "1"): services.get_routes_v1,
  ("get_home", "2"): services.get_home_v2,
  ("get_routes", "2"): services.get_routes_v2,
}
