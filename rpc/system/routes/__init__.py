from .services import (system_routes_delete_route_v1,
                       system_routes_get_routes_v1,
                       system_routes_set_route_V1)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_routes", "1"): system_routes_get_routes_v1,
  ("set_route", "1"): system_routes_set_route_V1,
  ("delete_route", "1"): system_routes_delete_route_v1
}

