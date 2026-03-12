from .accounts.handler import handle_accounts_request
from .dimensions.handler import handle_dimensions_request
from .numbers.handler import handle_numbers_request
from .periods.handler import handle_periods_request
from .staging.handler import handle_staging_request


HANDLERS: dict[str, callable] = {
  "accounts": handle_accounts_request,
  "dimensions": handle_dimensions_request,
  "numbers": handle_numbers_request,
  "periods": handle_periods_request,
  "staging": handle_staging_request,
}


REQUIRED_ROLES: dict[str, str] = {
  "accounts": "ROLE_FINANCE_ADMIN",
  "dimensions": "ROLE_FINANCE_ADMIN",
  "numbers": "ROLE_FINANCE_ADMIN",
  "periods": "ROLE_FINANCE_ADMIN",
  "staging": "ROLE_FINANCE_ADMIN",
}


FORBIDDEN_DETAILS: dict[str, str] = {
  "accounts": "Forbidden",
  "dimensions": "Forbidden",
  "numbers": "Forbidden",
  "periods": "Forbidden",
  "staging": "Forbidden",
}
