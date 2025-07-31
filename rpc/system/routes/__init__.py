from .services import delete_route_v1, list_routes_v1, set_route_v1

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): list_routes_v1,
  ("set", "1"): set_route_v1,
  ("delete", "1"): delete_route_v1
}
