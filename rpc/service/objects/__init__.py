"""Service objects RPC namespace.

Requires ROLE_SERVICE_ADMIN.
"""

from .services import (
  service_objects_create_tree_node_v1,
  service_objects_delete_database_column_v1,
  service_objects_delete_database_table_v1,
  service_objects_delete_module_method_v1,
  service_objects_delete_tree_node_v1,
  service_objects_delete_type_v1,
  service_objects_get_method_contract_v1,
  service_objects_get_module_methods_v1,
  service_objects_get_page_tree_v1,
  service_objects_get_type_controls_v1,
  service_objects_list_components_v1,
  service_objects_move_tree_node_v1,
  service_objects_read_object_tree_children_v1,
  service_objects_read_object_tree_detail_v1,
  service_objects_upsert_database_column_v1,
  service_objects_update_tree_node_v1,
  service_objects_upsert_database_table_v1,
  service_objects_upsert_module_method_v1,
  service_objects_upsert_module_v1,
  service_objects_upsert_type_v1,
)


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("read_object_tree_children", "1"): service_objects_read_object_tree_children_v1,
  ("read_object_tree_detail", "1"): service_objects_read_object_tree_detail_v1,
  ("upsert_database_table", "1"): service_objects_upsert_database_table_v1,
  ("delete_database_table", "1"): service_objects_delete_database_table_v1,
  ("upsert_database_column", "1"): service_objects_upsert_database_column_v1,
  ("delete_database_column", "1"): service_objects_delete_database_column_v1,
  ("upsert_type", "1"): service_objects_upsert_type_v1,
  ("delete_type", "1"): service_objects_delete_type_v1,
  ("get_type_controls", "1"): service_objects_get_type_controls_v1,
  ("get_module_methods", "1"): service_objects_get_module_methods_v1,
  ("upsert_module", "1"): service_objects_upsert_module_v1,
  ("upsert_module_method", "1"): service_objects_upsert_module_method_v1,
  ("delete_module_method", "1"): service_objects_delete_module_method_v1,
  ("get_method_contract", "1"): service_objects_get_method_contract_v1,
  ("get_page_tree", "1"): service_objects_get_page_tree_v1,
  ("list_components", "1"): service_objects_list_components_v1,
  ("create_tree_node", "1"): service_objects_create_tree_node_v1,
  ("update_tree_node", "1"): service_objects_update_tree_node_v1,
  ("delete_tree_node", "1"): service_objects_delete_tree_node_v1,
  ("move_tree_node", "1"): service_objects_move_tree_node_v1,
}
