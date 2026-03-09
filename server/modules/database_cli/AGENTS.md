# Database CLI AGENT Instructions

Guidance for `server/modules/database_cli/` tooling in the reflection-era architecture.

---

## What this layer IS

- Operator/developer tooling for interactive DB workflows.
- A thin CLI surface that bootstraps `EnvModule` → `DbModule` → `DatabaseCliModule`.
- A module-driven interface where business actions dispatch through `self.db.run(...)`
  using reflection queryregistry operations.

## What this layer is NOT

- Not a local schema registry documentation source.
- Not a place to define canonical data-access operations (those live in
  `queryregistry/reflection/`).
- Not a compatibility shim for legacy registry op names or old command aliases.

---

## Key files

- `server/modules/database_cli/cli.py`
  - REPL command loop and minimal lifecycle bootstrap.
  - Handles command parsing and delegates business actions to `DatabaseCliModule`.
- `server/modules/database_cli/mssql_cli.py`
  - Provider-specific raw connection helper for ad-hoc/raw SQL execution only.
- `server/modules/database_cli_module.py`
  - CLI business logic and all reflection-domain dispatch via `self.db.run(...)`.
- `scripts/run_cli.py`
  - Canonical CLI entry point.

Adjacent guidance:
- `server/modules/AGENTS.md` for module lifecycle boundaries.
- `queryregistry/AGENTS.md` for canonical query dispatch conventions.
- `scripts/AGENTS.md` for script-entrypoint expectations.

---

## Architecture expectations

- Schema metadata is owned by `queryregistry/reflection/` operations, not local markdown docs.
- EDT mappings are owned by the `system_edt_mappings` table and the
  `queryregistry/reflection/schema/` subdomain.
- Prefer reflection queryregistry requests for schema and data workflows.
- Keep command behavior explicit and aligned with the current REPL command set.

---

## Naming conventions

- Schema metadata fields should follow `element_*` naming.
- Primary IDs and FK references use `recid` with `bigint` semantics.
- Temporal metadata columns use `datetimeoffset` with UTC defaults.

---

## Anti-patterns (forbidden)

- Adding aliases to preserve legacy operation names.
- Implementing module actions that bypass `self.db.run(...)` and reflection ops.
- Embedding domain business logic into raw SQL helper code.
- Re-introducing local documentation as a substitute for reflection metadata sources.
