from .services import (
  finance_journals_create_v1,
  finance_journals_get_lines_v1,
  finance_journals_get_v1,
  finance_journals_list_v1,
  finance_journals_post_v1,
  finance_journals_reverse_v1,
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): finance_journals_list_v1,
  ("get", "1"): finance_journals_get_v1,
  ("get_lines", "1"): finance_journals_get_lines_v1,
  ("create", "1"): finance_journals_create_v1,
  ("post", "1"): finance_journals_post_v1,
  ("reverse", "1"): finance_journals_reverse_v1,
}
