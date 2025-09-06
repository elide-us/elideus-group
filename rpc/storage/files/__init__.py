"""File storage RPC namespace.

Requires ROLE_STORAGE.
"""

from .services import (
  storage_files_get_files_v1,
  storage_files_upload_files_v1,
  storage_files_delete_files_v1,
  storage_files_set_gallery_v1,
  storage_files_create_folder_v1,
  storage_files_move_file_v1,
  storage_files_refresh_cache_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_files", "1"): storage_files_get_files_v1,
  ("upload_files", "1"): storage_files_upload_files_v1,
  ("delete_files", "1"): storage_files_delete_files_v1,
  ("set_gallery", "1"): storage_files_set_gallery_v1,
  ("create_folder", "1"): storage_files_create_folder_v1,
  ("move_file", "1"): storage_files_move_file_v1,
  ("refresh_cache", "1"): storage_files_refresh_cache_v1,
}

