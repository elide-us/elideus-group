from .services import (
  finance_reporting_credit_lot_summary_v1,
  finance_reporting_journal_summary_v1,
  finance_reporting_period_status_v1,
  finance_reporting_trial_balance_v1,
)

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("trial_balance", "1"): finance_reporting_trial_balance_v1,
  ("journal_summary", "1"): finance_reporting_journal_summary_v1,
  ("period_status", "1"): finance_reporting_period_status_v1,
  ("credit_lot_summary", "1"): finance_reporting_credit_lot_summary_v1,
}
