from .services import (
  finance_periods_close_v1,
  finance_periods_delete_v1,
  finance_periods_generate_calendar_v1,
  finance_periods_get_v1,
  finance_periods_list_by_year_v1,
  finance_periods_list_close_blockers_v1,
  finance_periods_list_v1,
  finance_periods_lock_v1,
  finance_periods_reopen_v1,
  finance_periods_unlock_v1,
  finance_periods_upsert_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): finance_periods_list_v1,
  ("list_by_year", "1"): finance_periods_list_by_year_v1,
  ("get", "1"): finance_periods_get_v1,
  ("close", "1"): finance_periods_close_v1,
  ("reopen", "1"): finance_periods_reopen_v1,
  ("lock", "1"): finance_periods_lock_v1,
  ("unlock", "1"): finance_periods_unlock_v1,
  ("list_close_blockers", "1"): finance_periods_list_close_blockers_v1,
  ("upsert", "1"): finance_periods_upsert_v1,
  ("delete", "1"): finance_periods_delete_v1,
  ("generate_calendar", "1"): finance_periods_generate_calendar_v1,
}
