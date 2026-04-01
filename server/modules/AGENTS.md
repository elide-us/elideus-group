# Server Modules AGENT Instructions

Guidance for runtime services under `server/modules/`.

---

## What modules ARE

- The **application/business logic layer** of the server.
- Runtime service objects with explicit lifecycle (`startup`, `shutdown`).
- `BaseModule` subclasses that are auto-discovered by `ModuleManager`.
- The place where decisions are made, workflows are orchestrated, and application
  rules are enforced.
- Callers of `queryregistry/` for data access translation while keeping business
  logic in modules.

---

## Key files

- `server/modules/__init__.py`
  - `BaseModule` contract.
  - `mark_ready()` / `on_ready()` readiness synchronization.
  - `ModuleManager` auto-discovery of `*_module.py` files and `CamelCaseModule` classes.
- `server/lifespan.py` – module manager startup/shutdown integration.
- `server/modules/db_module.py` – DB runtime dispatch and migration-aware behavior.

Adjacent guidance:
- `server/modules/providers/AGENTS.md` for provider boundaries.
- `queryregistry/AGENTS.md` for canonical query operation and dispatcher patterns.

---

## Required patterns

- Inherit from `BaseModule` for all modules.
- Set readiness with `mark_ready()` after startup initialization completes.
- Await dependent modules with `await other_module.on_ready()` before use.
- Let `ModuleManager` discovery/load modules; follow naming contract:
  - file: `snake_case_module.py`
  - class: `CamelCaseModule`
- All data access goes through `self.db.run(request_builder())`. See PATTERNS.md §3.2
  for the canonical pattern.
- Module business methods return the RPC response Pydantic model (`rpc/**/models.py`)
  directly. The service function passes it through without transformation.
  See PATTERNS.md §3.3 for the model ownership contract.

---

## Naming and data conventions

- Preserve DB naming conventions in module-facing payloads and docs:
  - `element_*` metadata fields.
  - `recid` values as `bigint` identifiers.
  - `datetimeoffset` for temporal audit columns.
