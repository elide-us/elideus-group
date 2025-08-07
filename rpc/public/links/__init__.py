from .services import (
  public_links_get_home_links_v1,
  public_links_get_navbar_routes_v1
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_home_links", "1"): public_links_get_home_links_v1,
  ("get_navbar_routes", "1"): public_links_get_navbar_routes_v1,
}

