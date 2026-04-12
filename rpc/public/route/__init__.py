from .services import (
  public_route_load_path_v1,
  public_route_read_navigation_v1,
  public_route_read_object_tree_categories_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("load_path", "1"): public_route_load_path_v1,
  ("read_navigation", "1"): public_route_read_navigation_v1,
  ("read_object_tree_categories", "1"): public_route_read_object_tree_categories_v1,
}
