"""Finance status code constants.

These values must stay in sync with the finance_status_codes table.
Management of status codes is via Finance Admin UI → status codes table.
"""

# Import statuses (finance_staging_imports.element_status)
IMPORT_PENDING = 0
IMPORT_COMPLETED = 1
IMPORT_FAILED = 2
IMPORT_PROMOTED = 3
IMPORT_APPROVED = 4
IMPORT_REJECTED = 5

# Journal statuses (finance_journals.element_status)
JOURNAL_DRAFT = 0
JOURNAL_POSTED = 1
JOURNAL_REVERSED = 2

# Period statuses (finance_periods.element_status)
PERIOD_OPEN = 1
PERIOD_CLOSED = 2
PERIOD_LOCKED = 3

# Period close types (finance_periods.element_close_type)
CLOSE_TYPE_NONE = 0
CLOSE_TYPE_QUARTERLY = 1
CLOSE_TYPE_ANNUAL = 2

# Generic element status
ELEMENT_INACTIVE = 0
ELEMENT_ACTIVE = 1

# Credit lot statuses
CREDIT_LOT_ACTIVE = 1
CREDIT_LOT_EXHAUSTED = 2
CREDIT_LOT_EXPIRED = 3
