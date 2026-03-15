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
