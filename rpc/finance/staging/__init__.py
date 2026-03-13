from .services import (
  finance_staging_import_v1,
  finance_staging_list_details_v1,
  finance_staging_list_imports_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("import", "1"): finance_staging_import_v1,
  ("list_imports", "1"): finance_staging_list_imports_v1,
  ("list_details", "1"): finance_staging_list_details_v1,
}
