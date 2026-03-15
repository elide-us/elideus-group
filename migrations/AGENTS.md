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
