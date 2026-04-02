"""Service reflection RPC namespace.

Requires ROLE_SERVICE_ADMIN.
"""

from .services import (
  service_reflection_describe_table_v1,
  service_reflection_dump_table_v1,
  service_reflection_get_full_schema_v1,
  service_reflection_get_schema_version_v1,
  service_reflection_list_domains_v1,
  service_reflection_list_edt_mappings_v1,
  service_reflection_list_rpc_endpoints_v1,
  service_reflection_list_tables_v1,
  service_reflection_list_views_v1,
  service_reflection_query_info_schema_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("list_tables", "1"): service_reflection_list_tables_v1,
  ("describe_table", "1"): service_reflection_describe_table_v1,
  ("list_views", "1"): service_reflection_list_views_v1,
  ("get_full_schema", "1"): service_reflection_get_full_schema_v1,
  ("get_schema_version", "1"): service_reflection_get_schema_version_v1,
  ("dump_table", "1"): service_reflection_dump_table_v1,
  ("query_info_schema", "1"): service_reflection_query_info_schema_v1,
  ("list_domains", "1"): service_reflection_list_domains_v1,
  ("list_edt_mappings", "1"): service_reflection_list_edt_mappings_v1,
  ("list_rpc_endpoints", "1"): service_reflection_list_rpc_endpoints_v1,
}
