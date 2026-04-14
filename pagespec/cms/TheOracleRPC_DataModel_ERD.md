# TheOracleRPC — Data Model ERD

## CMS Rendering Engine

Components, composition trees, properties (3-layer resolution), pages, data bindings, and routes.

```mermaid
erDiagram
  components ||--o{ component_tree : "ref_component_guid"
  component_tree ||--o{ component_tree : "ref_parent_guid (self)"
  component_tree ||--o{ tree_node_properties : "ref_tree_node_guid"
  components ||--o{ component_properties : "ref_component_guid"
  properties ||--o{ component_properties : "ref_property_guid"
  properties ||--o{ tree_node_properties : "ref_property_guid"
  types ||--o{ properties : "ref_type_guid"
  types ||--o{ components : "ref_default_type_guid"
  types ||--o{ type_controls : "ref_type_guid"
  components ||--o{ type_controls : "ref_component_guid"
  pages ||--o{ component_tree : "ref_page_guid"
  pages ||--o{ page_data_bindings : "ref_page_guid"
  component_tree ||--o{ page_data_bindings : "ref_component_node_guid"
  pages ||--o| rpc_models : "ref_derived_model_guid"
  routes ||--o| pages : "ref_page_guid"
  routes ||--o| component_tree : "ref_root_node_guid"
  components {
    uuid key_guid PK
    string pub_name
    string pub_category
    uuid ref_default_type_guid FK
  }
  component_tree {
    uuid key_guid PK
    uuid ref_parent_guid FK
    uuid ref_component_guid FK
    uuid ref_page_guid FK
    string pub_label
    string pub_field_binding
    int pub_sequence
  }
  properties {
    uuid key_guid PK
    string pub_name
    string pub_category
    uuid ref_type_guid FK
    string pub_default_value
  }
  component_properties {
    uuid key_guid PK
    uuid ref_component_guid FK
    uuid ref_property_guid FK
    string pub_value
  }
  tree_node_properties {
    uuid key_guid PK
    uuid ref_tree_node_guid FK
    uuid ref_property_guid FK
    string pub_value
  }
  pages {
    uuid key_guid PK
    string pub_slug
    uuid ref_root_component_guid FK
    uuid ref_derived_model_guid FK
    text pub_derived_query
  }
  page_data_bindings {
    uuid key_guid PK
    uuid ref_page_guid FK
    uuid ref_component_node_guid FK
    string pub_source_type
    string pub_alias
    uuid ref_column_guid FK
    uuid ref_method_guid FK
  }
  routes {
    uuid key_guid PK
    string pub_path
    uuid ref_page_guid FK
    uuid ref_required_role_guid FK
  }
  types {
    uuid key_guid PK
    string pub_name
    string pub_mssql_type
    string pub_python_type
    string pub_typescript_type
  }
  type_controls {
    uuid key_guid PK
    uuid ref_type_guid FK
    uuid ref_component_guid FK
    bit pub_is_default
  }
  rpc_models {
    uuid key_guid PK
    string pub_name
    int pub_version
  }
```

---

## RPC Dispatch Surface

Domains, subdomains, functions, and their method bindings. The data-driven dispatch graph.

```mermaid
erDiagram
  rpc_domains ||--o{ rpc_subdomains : "ref_domain_guid"
  rpc_subdomains ||--o{ rpc_functions : "ref_subdomain_guid"
  rpc_functions ||--o| module_methods : "ref_method_guid"
  auth_roles ||--o{ rpc_domains : "ref_required_role_guid"
  auth_entitlements ||--o{ rpc_subdomains : "ref_required_entitlement_guid"
  rpc_domains {
    uuid key_guid PK
    string pub_name
    uuid ref_required_role_guid FK
  }
  rpc_subdomains {
    uuid key_guid PK
    string pub_name
    uuid ref_domain_guid FK
    uuid ref_required_entitlement_guid FK
  }
  rpc_functions {
    uuid key_guid PK
    string pub_name
    int pub_version
    uuid ref_subdomain_guid FK
    uuid ref_method_guid FK
  }
  module_methods {
    uuid key_guid PK
    string pub_name
    uuid ref_module_guid FK
  }
  auth_roles {
    uuid key_guid PK
    string pub_name
  }
  auth_entitlements {
    uuid key_guid PK
    string pub_name
  }
```

---

## Module System

Modules, methods, contracts, queries, and gateway bindings. The server-side execution graph.

```mermaid
erDiagram
  modules ||--o{ module_methods : "ref_module_guid"
  module_methods ||--o{ module_contracts : "ref_method_guid"
  module_methods ||--o{ rpc_functions : "ref_method_guid"
  module_methods ||--o{ gateway_method_bindings : "ref_method_guid"
  modules ||--o{ queries : "ref_module_guid"
  modules ||--o{ io_gateways : "ref_module_guid"
  io_gateways ||--o{ gateway_method_bindings : "ref_gateway_guid"
  rpc_models ||--o{ module_contracts : "ref_request_model_guid"
  rpc_models ||--o{ module_contracts : "ref_response_model_guid"
  rpc_models ||--o{ rpc_model_fields : "ref_model_guid"
  types ||--o{ rpc_model_fields : "ref_type_guid"
  modules {
    uuid key_guid PK
    string pub_name
    string pub_state_attr
    string pub_module_path
  }
  module_methods {
    uuid key_guid PK
    uuid ref_module_guid FK
    string pub_name
    uuid ref_request_model_guid FK
    uuid ref_response_model_guid FK
  }
  module_contracts {
    uuid key_guid PK
    uuid ref_module_guid FK
    uuid ref_method_guid FK
    uuid ref_request_model_guid FK
    uuid ref_response_model_guid FK
  }
  queries {
    uuid key_guid PK
    string pub_name
    text pub_query_text
    uuid ref_module_guid FK
  }
  io_gateways {
    uuid key_guid PK
    string pub_name
    uuid ref_module_guid FK
  }
  gateway_method_bindings {
    uuid key_guid PK
    uuid ref_gateway_guid FK
    uuid ref_method_guid FK
    string pub_operation_name
  }
  rpc_models {
    uuid key_guid PK
    string pub_name
    int pub_version
  }
  rpc_model_fields {
    uuid key_guid PK
    uuid ref_model_guid FK
    string pub_name
    uuid ref_type_guid FK
  }
  rpc_functions {
    uuid key_guid PK
    string pub_name
    uuid ref_method_guid FK
  }
  types {
    uuid key_guid PK
    string pub_name
  }
```

---

## Database Reflection

Tables, columns, types, constraints, indexes. The self-describing schema.

```mermaid
erDiagram
  database_tables ||--o{ database_columns : "ref_table_guid"
  database_tables ||--o{ database_indexes : "ref_table_guid"
  database_tables ||--o{ database_constraints : "ref_table_guid"
  database_tables ||--o{ database_constraints : "ref_referenced_table_guid"
  database_columns ||--o{ database_constraints : "ref_column_guid"
  database_columns ||--o{ database_constraints : "ref_referenced_column_guid"
  types ||--o{ database_columns : "ref_type_guid"
  tree_categories ||--o{ tree_category_tables : "ref_category_guid"
  database_tables ||--o{ tree_category_tables : "ref_table_guid"
  tree_categories ||--o{ tree_subcategories : "ref_category_guid"
  database_tables {
    uuid key_guid PK
    string pub_name
    string pub_schema
  }
  database_columns {
    uuid key_guid PK
    uuid ref_table_guid FK
    uuid ref_type_guid FK
    string pub_name
    int pub_ordinal
    bit pub_is_primary_key
    bit pub_is_nullable
  }
  database_constraints {
    uuid key_guid PK
    uuid ref_table_guid FK
    uuid ref_column_guid FK
    uuid ref_referenced_table_guid FK
    uuid ref_referenced_column_guid FK
  }
  database_indexes {
    uuid key_guid PK
    uuid ref_table_guid FK
    string pub_name
    string pub_columns
  }
  types {
    uuid key_guid PK
    string pub_name
    string pub_mssql_type
  }
  tree_categories {
    uuid key_guid PK
    string pub_name
    string pub_builder_component
  }
  tree_category_tables {
    uuid key_guid PK
    uuid ref_category_guid FK
    uuid ref_table_guid FK
    bit pub_is_root_table
  }
  tree_subcategories {
    uuid key_guid PK
    uuid ref_category_guid FK
    string pub_name
  }
```

---

## Identity and Access

Users, roles, entitlements, sessions, tokens, OAuth providers, gateways.

```mermaid
erDiagram
  users ||--o{ user_roles : "ref_user_guid"
  users ||--o{ user_entitlements : "ref_user_guid"
  users ||--o{ user_auth : "ref_user_guid"
  users ||--o{ sessions : "ref_user_guid"
  auth_roles ||--o{ user_roles : "ref_role_guid"
  auth_entitlements ||--o{ user_entitlements : "ref_entitlement_guid"
  auth_providers ||--o{ user_auth : "ref_provider_guid"
  sessions ||--o{ session_tokens : "ref_session_guid"
  sessions ||--o{ session_devices : "ref_session_guid"
  enum_categories ||--o{ enum_values : "ref_category_guid"
  enum_values ||--o{ sessions : "ref_session_type_guid"
  enum_values ||--o{ session_tokens : "ref_token_type_guid"
  io_gateways ||--o{ gateway_identity_providers : "ref_gateway_guid"
  users {
    uuid key_guid PK
    string pub_display
    string pub_email
  }
  auth_roles {
    uuid key_guid PK
    string pub_name
  }
  auth_entitlements {
    uuid key_guid PK
    string pub_name
  }
  auth_providers {
    uuid key_guid PK
    string pub_name
    string pub_strategy
  }
  sessions {
    uuid key_guid PK
    uuid ref_user_guid FK
    uuid ref_session_type_guid FK
    bit pub_is_active
  }
  session_tokens {
    uuid key_guid PK
    uuid ref_session_guid FK
    uuid ref_token_type_guid FK
    string pub_token_hash
  }
  session_devices {
    uuid key_guid PK
    uuid ref_session_guid FK
    string pub_device_fingerprint
  }
  user_roles {
    uuid ref_user_guid FK
    uuid ref_role_guid FK
  }
  user_entitlements {
    uuid ref_user_guid FK
    uuid ref_entitlement_guid FK
  }
  user_auth {
    uuid ref_user_guid FK
    uuid ref_provider_guid FK
    bit pub_is_linked
  }
  io_gateways {
    uuid key_guid PK
    string pub_name
  }
  gateway_identity_providers {
    uuid key_guid PK
    uuid ref_gateway_guid FK
  }
  enum_categories {
    uuid key_guid PK
    string pub_name
  }
  enum_values {
    uuid key_guid PK
    uuid ref_category_guid FK
    string pub_name
  }
```
