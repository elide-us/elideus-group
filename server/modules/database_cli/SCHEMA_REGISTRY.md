# Schema Registry

## Purpose

The schema registry makes the database self-describing so tooling can generate full
"create from blank" SQL without ODBC metadata introspection.

By combining:
- `system_edt_mappings` (logical type dictionary), and
- `system_schema_*` tables (table/column/index/FK topology),

a CLI/GUI can emit deterministic `CREATE TABLE`, `CREATE INDEX`, and foreign-key
constraint scripts from data already stored in the database.

## Registry Tables

### `system_schema_tables`
Catalog of known database tables.

- `recid` bigint primary key
- `element_name` table name
- `element_schema` schema name (defaults to `dbo`)
- `element_description` optional docs
- `element_created_on` / `element_modified_on` timestamps
- unique key: `(element_schema, element_name)`

### `system_schema_columns`
Column definitions per table.

- `recid` bigint primary key
- `tables_recid` → `system_schema_tables.recid`
- `edt_recid` → `system_edt_mappings.recid`
- `element_name` column name
- `element_ordinal` position in table
- `element_nullable` nullable flag
- `element_default` default expression as text
- `element_max_length` optional length override
- `element_is_primary_key` PK membership flag
- `element_is_identity` identity/auto-number flag
- `element_description` optional docs
- `element_created_on` / `element_modified_on` timestamps
- unique key: `(tables_recid, element_name)`
- index: `(tables_recid, element_ordinal)`

### `system_schema_indexes`
Indexes and uniqueness definitions.

- `recid` bigint primary key
- `tables_recid` → `system_schema_tables.recid`
- `element_name` index/constraint name
- `element_columns` comma-separated column list
- `element_is_unique` unique flag
- `element_created_on` / `element_modified_on` timestamps
- unique key: `(tables_recid, element_name)`

### `system_schema_foreign_keys`
Foreign-key relationships.

- `recid` bigint primary key
- `tables_recid` source table (`system_schema_tables.recid`)
- `element_column_name` source column
- `referenced_tables_recid` target table (`system_schema_tables.recid`)
- `element_referenced_column` target column
- `element_created_on` / `element_modified_on` timestamps
- unique key: `(tables_recid, element_column_name)`

## How script generation works

1. Read tables from `system_schema_tables`.
2. Read columns for each table from `system_schema_columns` ordered by
   `element_ordinal`.
3. Resolve each column type through `system_edt_mappings` (plus
   `element_max_length` override when present).
4. Build PK/identity/default/nullability from column flags.
5. Emit secondary indexes from `system_schema_indexes`.
6. Emit relationships from `system_schema_foreign_keys`.

This avoids provider-specific introspection paths and keeps schema generation
consistent across runtime environments.
