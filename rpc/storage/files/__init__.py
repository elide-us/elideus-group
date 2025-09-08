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
  storage_files_rename_file_v1,
  storage_files_get_link_v1,
  storage_files_get_metadata_v1,
  storage_files_get_folder_files_v1,
  storage_files_delete_folder_v1,
  storage_files_create_user_folder_v1,
  storage_files_get_usage_v1,
  storage_files_get_public_files_v1,
  storage_files_get_moderation_files_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_files", "1"): storage_files_get_files_v1,
  ("upload_files", "1"): storage_files_upload_files_v1,
  ("delete_files", "1"): storage_files_delete_files_v1,
  ("set_gallery", "1"): storage_files_set_gallery_v1,
  ("create_folder", "1"): storage_files_create_folder_v1,
  ("move_file", "1"): storage_files_move_file_v1,
  ("rename_file", "1"): storage_files_rename_file_v1,
  ("get_link", "1"): storage_files_get_link_v1,
  ("get_metadata", "1"): storage_files_get_metadata_v1,
  ("get_folder_files", "1"): storage_files_get_folder_files_v1,
  ("delete_folder", "1"): storage_files_delete_folder_v1,
  ("create_user_folder", "1"): storage_files_create_user_folder_v1,
  ("get_usage", "1"): storage_files_get_usage_v1,
  ("get_public_files", "1"): storage_files_get_public_files_v1,
  ("get_moderation_files", "1"): storage_files_get_moderation_files_v1,
}

