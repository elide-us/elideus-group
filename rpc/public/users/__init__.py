from .services import (
  public_users_get_profile_v1,
  public_users_get_published_files_v1,
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_profile", "1"): public_users_get_profile_v1,
  ("get_published_files", "1"): public_users_get_published_files_v1,
}
