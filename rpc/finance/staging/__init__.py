from .services import (
  finance_staging_approve_v1,
  finance_staging_delete_import_v1,
  finance_staging_import_invoices_v1,
  finance_staging_import_v1,
  finance_staging_list_details_v1,
  finance_staging_list_imports_v1,
  finance_staging_list_line_items_v1,
  finance_staging_promote_v1,
  finance_staging_reject_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("approve", "1"): finance_staging_approve_v1,
  ("delete_import", "1"): finance_staging_delete_import_v1,
  ("import", "1"): finance_staging_import_v1,
  ("import_invoices", "1"): finance_staging_import_invoices_v1,
  ("list_imports", "1"): finance_staging_list_imports_v1,
  ("list_details", "1"): finance_staging_list_details_v1,
  ("list_line_items", "1"): finance_staging_list_line_items_v1,
  ("promote", "1"): finance_staging_promote_v1,
  ("reject", "1"): finance_staging_reject_v1,
}
