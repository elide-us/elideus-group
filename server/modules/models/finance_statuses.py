"""Finance status code constants.

These values must stay in sync with the finance_status_codes table.
Management of status codes is via Finance Admin UI → status codes table.
"""

# Import statuses (finance_staging_imports.element_status)
IMPORT_PENDING = 0
IMPORT_APPROVED = 1
IMPORT_FAILED = 2
IMPORT_PROMOTED = 3
IMPORT_PENDING_APPROVAL = 4
IMPORT_REJECTED = 5

# Journal statuses (finance_journals.element_status)
JOURNAL_DRAFT = 0
JOURNAL_PENDING_APPROVAL = 1
JOURNAL_POSTED = 2
JOURNAL_REVERSED = 3

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


# Number sequence statuses (finance_numbers.element_sequence_status)
NUMBER_SEQUENCE_INACTIVE = 0
NUMBER_SEQUENCE_ACTIVE = 1

# Number sequence types (finance_numbers.element_sequence_type)
NUMBER_SEQUENCE_CONTINUOUS = 1
NUMBER_SEQUENCE_NON_CONTINUOUS = 2

# Product statuses (finance_products.element_status)
PRODUCT_INACTIVE = 0
PRODUCT_ACTIVE = 1

# Product journal config statuses (finance_product_journal_config.element_status)
PRODUCT_JOURNAL_CONFIG_DRAFT = 0
PRODUCT_JOURNAL_CONFIG_APPROVED = 1
PRODUCT_JOURNAL_CONFIG_ACTIVE = 2
PRODUCT_JOURNAL_CONFIG_CLOSED = 3
