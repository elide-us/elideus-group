from .services import (
  public_vars_get_ffmpeg_version_v1,
  public_vars_get_hostname_v1,
  public_vars_get_repo_v1,
  public_vars_get_version_v1,
  public_vars_get_odbc_version_v1
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_version", "1"): public_vars_get_version_v1,
  ("get_hostname", "1"): public_vars_get_hostname_v1,
  ("get_repo", "1"): public_vars_get_repo_v1,
  ("get_ffmpeg_version", "1"): public_vars_get_ffmpeg_version_v1,
  ("get_odbc_version", "1"): public_vars_get_odbc_version_v1
}

