from .services import public_gallery_get_public_files_v1

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_public_files", "1"): public_gallery_get_public_files_v1,
}
