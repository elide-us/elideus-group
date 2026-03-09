# Server Provider AGENT Instructions

Guidance for provider abstractions under `server/modules/providers/`.

---

## What providers ARE

- Infrastructure adapters for external systems (DB, auth, storage, social).
- Lifecycle-managed integrations created and owned by modules.
- The place for connection pooling, transaction boundaries, and protocol-specific I/O.

## What providers are NOT

- Not domain business logic.
- Not registry/domain dispatch map definitions.
- Not a place to introduce operation-name compatibility aliases.

---

## Database provider focus

Key files:
- `server/modules/providers/__init__.py` – `DbProviderBase` and shared provider contracts.
- `server/modules/providers/database/mssql_provider/__init__.py` – provider entrypoint,
  normalization, and queryregistry dispatch path.
- `server/modules/providers/database/mssql_provider/logic.py` – pool lifecycle and
  transaction context manager.

Patterns to preserve:
- Initialize and close pooled DB connections in provider `startup()` / `shutdown()`.
- Use provider-level helpers for execution flows such as:
  - `run_exec(...)` for command/rowcount-oriented operations.
  - `run_json_one(...)` for single-object JSON payload retrieval.
- Keep explicit transaction handling via context managers (`commit`/`rollback` behavior).
- Providers are shared by both registries during migration, but **new operations must target
  `queryregistry/` contracts**.

---

## Naming and schema conventions

- Keep DB payload conventions stable:
  - `element_*` metadata fields.
  - `recid` as `bigint` IDs.
  - `datetimeoffset` temporal values.

---

## Anti-patterns (forbidden)

- Adding provider-side aliases for legacy/new operation names.
- Silently swallowing provider exceptions; include contextual logs.
- Embedding domain routing rules in providers.
- Adding new work that depends on `server/registry/` as a target layer.

Adjacent guidance:
- `server/modules/AGENTS.md` for lifecycle and module boundaries.
- `queryregistry/AGENTS.md` for canonical registry dispatch and contracts.
- `server/registry/AGENTS.md` for legacy/deprecation constraints.
