from .services import (
    get_version_v1,
    get_hostname_v1,
    get_repo_v1,
    get_ffmpeg_version_v1
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_version", "1"): get_version_v1,
  ("get_hostname", "1"): get_hostname_v1,
  ("get_repo", "1"): get_repo_v1,
  ("get_ffmpeg_version", "1"): get_ffmpeg_version_v1
}
