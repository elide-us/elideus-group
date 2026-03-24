from .services import (
  finance_journals_approve_v1,
  finance_journals_create_v1,
  finance_journals_get_lines_v1,
  finance_journals_get_v1,
  finance_journals_list_v1,
  finance_journals_reject_v1,
  finance_journals_reverse_v1,
  finance_journals_submit_for_approval_v1,
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list", "1"): finance_journals_list_v1,
  ("get", "1"): finance_journals_get_v1,
  ("get_lines", "1"): finance_journals_get_lines_v1,
  ("create", "1"): finance_journals_create_v1,
  ("submit_for_approval", "1"): finance_journals_submit_for_approval_v1,
  ("approve", "1"): finance_journals_approve_v1,
  ("reject", "1"): finance_journals_reject_v1,
  ("reverse", "1"): finance_journals_reverse_v1,
}
