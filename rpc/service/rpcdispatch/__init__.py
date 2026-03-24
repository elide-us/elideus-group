"""Service rpcdispatch RPC namespace.

Requires ROLE_SERVICE_ADMIN.
"""

from .services import (
  service_rpcdispatch_list_domains_v1,
  service_rpcdispatch_list_functions_v1,
  service_rpcdispatch_list_model_fields_v1,
  service_rpcdispatch_list_models_v1,
  service_rpcdispatch_list_subdomains_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list_domains", "1"): service_rpcdispatch_list_domains_v1,
  ("list_subdomains", "1"): service_rpcdispatch_list_subdomains_v1,
  ("list_functions", "1"): service_rpcdispatch_list_functions_v1,
  ("list_models", "1"): service_rpcdispatch_list_models_v1,
  ("list_model_fields", "1"): service_rpcdispatch_list_model_fields_v1,
}
