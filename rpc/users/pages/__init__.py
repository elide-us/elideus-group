from .services import (
  users_pages_create_version_v1,
  users_pages_get_version_v1,
  users_pages_list_versions_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("create_version", "1"): users_pages_create_version_v1,
  ("list_versions", "1"): users_pages_list_versions_v1,
  ("get_version", "1"): users_pages_get_version_v1,
}
