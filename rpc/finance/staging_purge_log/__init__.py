from .services import finance_staging_purge_log_list_v1


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): finance_staging_purge_log_list_v1,
}
