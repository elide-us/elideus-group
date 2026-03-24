# Migrations

Human-run migration scripts that alter the database schema incrementally on top of the current baseline.

## Versioning

The repo root holds the current tagged release baseline:

- `v{Major}.{Minor}.{Patch}.{Build}_YYYYMMDD.sql` — full schema DDL
- `v{Major}.{Minor}.{Patch}.{Build}_seed_YYYYMMDD.sql` — seed data

Version format: `Major.Minor.Patch.Build`

- **Major** — breaking / incompatible platform changes
- **Minor** — feature releases
- **Patch / Schema** — incremental schema changes (migrations increment this)
- **Build** — automated increment by build system

## Naming

Migration files increment the Patch value from the root baseline. If the root is `v0.9.0.0`, migrations are:

```
v0.9.1.0_batch_jobs.sql
v0.9.2.0_journal_lines.sql
v0.9.3.0_credit_lots.sql
```

Always increment from the highest existing migration in this folder, not from the root.

Format: `v{Major}.{Minor}.{Patch}.0_{short_description}.sql`

## Rules

- Each file should be idempotent where possible
- Include all related DDL in one file (tables, views, indexes, constraints, seed data)
- Every migration must include seed data updates for the `system_schema` reflection tables alongside schema changes
- Do not modify root baseline files — those are regenerated at release time
- Keep descriptions short, lowercase, underscores in filenames

## Reflection registration in migrations

Every migration that creates tables must register them in the reflection
system (`system_schema_tables`, `system_schema_columns`,
`system_schema_indexes`, `system_schema_foreign_keys`).

### Use direct INSERTs, not INFORMATION_SCHEMA discovery

When a migration creates a table and registers its reflection in the same
file, use direct `INSERT ... VALUES` for `system_schema_columns` with
hardcoded `edt_recid` values from `system_edt_mappings`. Do NOT query
`INFORMATION_SCHEMA.COLUMNS` to discover the schema of a table you just
created in the same file — you already know the schema because you wrote it.

EDT mapping reference (from `system_edt_mappings`):

| edt_recid | element_name   | element_mssql_type       |
|-----------|----------------|--------------------------|
| 1         | INT32          | int                      |
| 2         | INT64          | bigint                   |
| 3         | INT64_IDENTITY | bigint identity(1,1)     |
| 4         | UUID           | uniqueidentifier         |
| 5         | BOOL           | bit                      |
| 7         | DATETIME_TZ    | datetimeoffset(7)        |
| 8         | STRING         | nvarchar                 |
| 9         | TEXT           | nvarchar(max)            |
| 11        | INT8           | tinyint                  |
| 12        | DATE           | date                     |
| 13        | DECIMAL_19_5   | decimal(19,5)            |

### Pattern
```sql
-- 1. Create the table
CREATE TABLE [dbo].[my_table] (...);
GO

-- 2. Register in system_schema_tables
INSERT INTO system_schema_tables (element_name, element_schema)
SELECT 'my_table', 'dbo'
WHERE NOT EXISTS (
  SELECT 1 FROM system_schema_tables
  WHERE element_name = 'my_table' AND element_schema = 'dbo'
);
GO

-- 3. Resolve the tables_recid
DECLARE @t BIGINT = (
  SELECT recid FROM system_schema_tables
  WHERE element_name = 'my_table' AND element_schema = 'dbo'
);

-- 4. Direct INSERT for columns (no INFORMATION_SCHEMA)
INSERT INTO system_schema_columns
  (tables_recid, edt_recid, element_name, element_ordinal,
   element_nullable, element_default, element_max_length,
   element_is_primary_key, element_is_identity)
VALUES
  (@t, 3, 'recid', 1, 0, NULL, NULL, 1, 1),
  (@t, 8, 'element_name', 2, 0, NULL, 128, 0, 0),
  ...
GO
```

## MSSQL Batch Separators

**Always use `GO` between statements that depend on each other.** MSSQL executes scripts in batches, and a batch boundary (`GO`) is required between:

- `CREATE TABLE` and any `ALTER TABLE` that references it (FKs, constraints)
- `CREATE TABLE` and any `INSERT` that targets it
- `ALTER TABLE` adding columns and any subsequent statements referencing those columns
- `CREATE INDEX` and any statements that depend on the indexed table existing
- `INSERT INTO` seed tables that use subselects against tables created earlier in the same script

Without `GO`, SSMS and `sqlcmd` will fail because the parser resolves the entire batch before execution and cannot see objects created within the same batch.

Example:
```sql
CREATE TABLE [dbo].[my_table] (
  [recid] BIGINT IDENTITY(1,1) NOT NULL,
  CONSTRAINT [PK_my_table] PRIMARY KEY ([recid])
);
GO

ALTER TABLE [dbo].[my_table] ADD [element_name] NVARCHAR(128) NOT NULL;
GO

INSERT INTO [dbo].[my_table] ([element_name]) VALUES ('example');
GO
```
