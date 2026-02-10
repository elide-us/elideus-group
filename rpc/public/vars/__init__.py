from .services import public_vars_get_versions_v1


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_versions", "1"): public_vars_get_versions_v1,
}

