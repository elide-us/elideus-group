from . import services

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_version", "1"): services.get_version_v1,
  ("get_hostname", "1"): services.get_hostname_v1,
  ("get_repo", "1"): services.get_repo_v1,
  ("get_version", "2"): services.get_version_v2,
  ("get_hostname", "2"): services.get_hostname_v2,
  ("get_repo", "2"): services.get_repo_v2,
  ("get_ffmpeg_version", "1"): services.get_ffmpeg_version_v1,
}
