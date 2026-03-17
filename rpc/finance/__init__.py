from .accounts.handler import handle_accounts_request
from .credit_lots.handler import handle_credit_lots_request
from .dimensions.handler import handle_dimensions_request
from .journals.handler import handle_journals_request
from .numbers.handler import handle_numbers_request
from .periods.handler import handle_periods_request
from .reporting.handler import handle_reporting_request
from .staging.handler import handle_staging_request
from .staging_account_map.handler import handle_staging_account_map_request
from .staging_purge_log.handler import handle_staging_purge_log_request
from .vendors.handler import handle_vendors_request


HANDLERS: dict[str, callable] = {
  "accounts": handle_accounts_request,
  "credit_lots": handle_credit_lots_request,
  "dimensions": handle_dimensions_request,
  "journals": handle_journals_request,
  "numbers": handle_numbers_request,
  "periods": handle_periods_request,
  "reporting": handle_reporting_request,
  "staging": handle_staging_request,
  "staging_account_map": handle_staging_account_map_request,
  "staging_purge_log": handle_staging_purge_log_request,
  "vendors": handle_vendors_request,
}
