# Database CLI User Guide

## Overview

The Database CLI is an interactive REPL for schema and data maintenance tasks.
It bootstraps a minimal application lifecycle in this order:

1. `EnvModule`
2. `DbModule`
3. `DatabaseCliModule`

Once bootstrapped, command execution is delegated into `DatabaseCliModule`,
which dispatches operations through the reflection queryregistry domain via
`self.db.run(...)`.

## Prerequisites

Before running the CLI, ensure:

- `AZURE_SQL_CONNECTION_STRING` is set in your environment.
- Python dependencies for this repository are installed.
- Your current working directory is the repository root.

## Run the CLI

```bash
python scripts/run_cli.py
```

You should see the prompt:

```text
cli>
```

## Commands

| Command | Description |
|---|---|
| `help` | Show available commands. |
| `list tables` | List all tables as `schema.table` from reflection metadata. |
| `schema dump [name]` | Export schema SQL from reflection metadata to a file. Uses `name` as file prefix (default: `schema`). |
| `schema apply <file>` | Apply a SQL file in `GO`-delimited batches. |
| `dump data [name]` | Dump table data SQL to a file with optional prefix (default: `dump_data`). |
| `update version major\|minor\|patch` | Bump semantic version, persist it, dump schema, commit, tag, and push in one flow. |
| `index all` | Rebuild indexes through the reflection data operation. |
| `<any other text>` | Treated as raw SQL and executed directly using the MSSQL raw connection helper. |
| `exit` / `quit` | Exit the REPL. |

## Version management walkthrough

`update version major|minor|patch` executes an end-to-end release workflow:

1. Reads current version from DB.
2. Computes the next version (`major`, `minor`, or `patch`).
3. Writes the new version to DB.
4. Dumps schema SQL using the new version as the filename prefix.
5. Runs Git automation:
   - `git add <schema_file>`
   - `git commit -m "Exported DB schema for <version>"`
   - `git tag <version>`
   - `git push origin <current_branch>`
   - `git push origin --tags`

This means a single CLI command can produce a version bump + schema snapshot +
release tag publication.

## Example session (minor release tag)

Example: moving from a `v0.8.x` line to `v0.9.0.0`.

```text
$ python scripts/run_cli.py
cli> help
cli> list tables
cli> update version minor
# CLI computes next version (for example, v0.9.0.0), writes it,
# exports schema file, commits, tags, and pushes.
cli> quit
```

If your local branch is behind remote, has uncommitted changes, or does not have
push permissions, the Git step will fail and should be resolved before retrying.

## Architecture quick reference

- `server/modules/database_cli/cli.py`
  - REPL loop and lifecycle bootstrap.
- `server/modules/database_cli_module.py`
  - Business workflows and reflection queryregistry dispatch.
- `server/modules/database_cli/mssql_cli.py`
  - Raw provider connection utility for ad-hoc SQL only.

Entry point:

- `scripts/run_cli.py`

## Reflection domain operation reference

The CLI and module dispatch through these reflection operations:

### Schema domain (`db:reflection:schema:*`)

- `db:reflection:schema:list_tables:1`
- `db:reflection:schema:list_columns:1`
- `db:reflection:schema:list_indexes:1`
- `db:reflection:schema:list_foreign_keys:1`
- `db:reflection:schema:list_views:1`
- `db:reflection:schema:get_full_schema:1`

### Data domain (`db:reflection:data:*`)

- `db:reflection:data:get_version:1`
- `db:reflection:data:update_version:1`
- `db:reflection:data:dump_table:1`
- `db:reflection:data:rebuild_indexes:1`
- `db:reflection:data:apply_batch:1`

## Canonical EDT primitives

The reflection-aligned canonical primitives are:

- `INT8`
- `INT32`
- `INT64`
- `INT64_IDENTITY`
- `UUID`
- `BOOL`
- `DATE`
- `DATETIME_TZ`
- `STRING`
- `TEXT`
