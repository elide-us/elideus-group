# Extended Data Type (EDT) Canonical Mapping

This document defines the canonical type system stored in `system_edt_mappings` for
cross-provider compatibility in the database CLI/provider abstraction layer.

## Schema Inventory (v0.7.2.0)

The following native SQL Server data types are used across all table and view-backed
objects in `scripts/v0.7.2.0_20250918.sql`:

- `int`
- `bigint`
- `bigint identity(1,1)`
- `bit`
- `uniqueidentifier`
- `datetime2`
- `datetimeoffset`
- `nvarchar(<n>)`
- `nvarchar(max)`
- `varchar(<n>)`

## `system_edt_mappings` Table Shape

- `recid bigint NOT NULL` (primary key)
- `element_name nvarchar(64) NOT NULL` (canonical EDT name)
- `element_mssql_type nvarchar(128) NOT NULL`
- `element_postgresql_type nvarchar(128) NOT NULL`
- `element_mysql_type nvarchar(128) NOT NULL`
- `element_python_type nvarchar(64) NOT NULL`
- `element_odbc_type_code int NOT NULL`
- `element_max_length int NULL`
- `element_notes nvarchar(2048) NULL`
- `element_created_on datetimeoffset DEFAULT (sysutcdatetime()) NOT NULL`
- `element_modified_on datetimeoffset DEFAULT (sysutcdatetime()) NOT NULL`
- unique index: `UQ_system_edt_mappings_name` on `element_name`

## Canonical EDT Rows

| element_name | element_mssql_type | element_postgresql_type | element_mysql_type | element_python_type | element_odbc_type_code |
| --- | --- | --- | --- | --- | --- |
| `INT32` | `int` | `integer` | `int` | `int` | `4` |
| `INT64` | `bigint` | `bigint` | `bigint` | `int` | `-5` |
| `INT64_IDENTITY` | `bigint identity(1,1)` | `bigserial` | `bigint auto_increment` | `int` | `-5` |
| `UUID` | `uniqueidentifier` | `uuid` | `char(36)` | `UUID` | `-11` |
| `BOOL` | `bit` | `boolean` | `boolean` | `bool` | `-7` |
| `DATETIME` | `datetime2(7)` | `timestamp` | `datetime(6)` | `datetime` | `93` |
| `DATETIME_TZ` | `datetimeoffset(7)` | `timestamptz` | `timestamp` | `datetime` | `-150` |
| `STRING` | `nvarchar` | `varchar` | `varchar` | `str` | `-9` |
| `TEXT` | `nvarchar(max)` | `text` | `longtext` | `str` | `-10` |
| `STRING_ASCII` | `varchar` | `varchar` | `varchar` | `str` | `12` |

## Provider Semantics to Watch

- **`DATETIME_TZ`**:
  - SQL Server `datetimeoffset` preserves explicit offset and is surfaced by some
    ODBC flows as type code `-150`, which can break naive metadata introspection.
  - PostgreSQL `timestamptz` stores UTC instant with timezone-aware conversion on read.
  - MySQL `timestamp` performs timezone normalization and has a narrower valid range
    than SQL Server/PostgreSQL.

- **`UUID`**:
  - SQL Server and PostgreSQL have native UUID types.
  - MySQL mapping defaults to `char(36)` for portability/readability; `binary(16)` can
    be used later for compact storage if API conversion policy is standardized.

- **`STRING` vs `TEXT`**:
  - SQL Server uses `nvarchar(<n>)` for bounded Unicode and `nvarchar(max)` for large text.
  - PostgreSQL and MySQL can use `varchar(<n>)` for bounded values and `text`/`longtext`
    for unbounded payloads.

- **Integer identity strategy**:
  - SQL Server uses `IDENTITY` on the column type.
  - PostgreSQL uses `serial`/`bigserial` pseudo-types.
  - MySQL uses `AUTO_INCREMENT` column attribute.

- **Boolean handling**:
  - SQL Server `bit` is integer-backed (0/1).
  - PostgreSQL and MySQL treat `boolean` semantically as true/false.

## Alignment with `database_cli`

The current `server/modules/database_cli` implementation lists table metadata via ODBC
and is intentionally provider-aware at the connector boundary. The EDT table gives that
layer a canonical normalization target without changing existing introspection logic in
this phase.
