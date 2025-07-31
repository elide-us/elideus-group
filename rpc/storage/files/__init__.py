from .services import (
    list_files_v1,
    delete_file_v1,
    upload_file_v1
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): list_files_v1,
  ("delete", "1"): delete_file_v1,
  ("upload", "1"): upload_file_v1,
}
