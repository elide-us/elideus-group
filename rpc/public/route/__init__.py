from .services import public_route_load_path_v1


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("load_path", "1"): public_route_load_path_v1,
}
