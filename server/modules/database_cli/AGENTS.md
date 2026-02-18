# Database CLI AGENT Instructions

Guidance for `server/modules/database_cli/` tooling and schema introspection flows.

---

## What this layer IS

- Operator/developer tooling for DB connectivity and schema metadata workflows.
- Utilities for schema-registry introspection and dump generation.
- A provider-aware CLI surface that complements runtime modules.

## What this layer is NOT

- Not the canonical query handler registry.
- Not a place for business-domain logic; business rules live in `server/modules/`.
- Not a place to define canonical data-access operations; those belong in `queryregistry/`.
- Not a compatibility shim layer for legacy registry naming.

---

## Key files

- `server/modules/database_cli/cli.py` – interactive REPL-style command loop.
- `server/modules/database_cli/mssql_cli.py` – MSSQL connection/reconnect/table-list helpers.
- `server/modules/database_cli/SCHEMA_REGISTRY.md` – schema registry table model and generation flow.
- `server/modules/database_cli/EDT_MAPPINGS.md` – canonical `system_edt_mappings` guidance.

Adjacent guidance:
- `server/modules/AGENTS.md` for module lifecycle boundaries.
- `server/modules/providers/AGENTS.md` for provider/pooling expectations.
- `queryregistry/AGENTS.md` for canonical query dispatch conventions.

---

## Schema registry expectations

- Treat schema registry as canonical metadata source for dump generation:
  - `system_schema_tables`
  - `system_schema_columns`
  - `system_schema_indexes`
  - `system_schema_foreign_keys`
- Type normalization is driven by `system_edt_mappings`.
- SQL dump generation should prefer registry-driven deterministic output over ad-hoc DB
  introspection when registry data is available.

---

## Naming conventions

- Schema metadata fields should follow `element_*` naming.
- Primary IDs and FK references use `recid` with `bigint` semantics.
- Temporal metadata columns use `datetimeoffset` with UTC defaults.

---

## Common patterns

- Keep connector logic provider-aware and isolated (`mssql_cli.py` now, future providers later).
- Fail fast with contextual logs when DSN/driver requirements are missing.
- Keep CLI command behavior explicit (`connect`, `reconnect`, `list tables`).

Future direction:
- Evolve toward a richer REPL/workbench interface while preserving stable command semantics
  and registry-first schema generation workflows.

---

## Anti-patterns (forbidden)

- Adding aliases to bridge old/new registry operation names.
- Embedding domain business logic into CLI helpers.
- Treating `server/registry/` as canonical for new schema/query features.
