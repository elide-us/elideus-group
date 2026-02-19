# Server AGENT Instructions

This file covers the FastAPI application entry point, startup sequence, and
other top-level server concerns.

---

## Layering Expectations

- Follow **ARCHITECTURE.md** for layer boundaries and responsibilities.
- Apply the server rule: Modules (business logic) → QueryRegistry
  (data-access translation) → Providers (connection/transport).

---

## Operational Guidance

- Changes to authentication or role resolution must preserve contracts in
  **AUTHENTICATION_DIAGRAMS.md**.
- Database loads and seed/migration handoffs must be delivered as `.sql` files
  for manual execution in **SSMS**.
- Keep logs structured with contextual module/service prefixes, and re-raise
  exceptions after logging so upstream callers receive accurate failures.

---

## Anti-Patterns To Avoid

- Do **not** bypass module boundaries from routers/RPC handlers.
- Do **not** perform blocking startup work without async-aware patterns.
- Do **not** add new query handlers to `server/registry/`; use
  `queryregistry/` for all new data access.

---

## Layer-Specific Guidance

- `server/modules/AGENTS.md` - module lifecycle and business logic patterns.
- `server/modules/providers/AGENTS.md` - provider boundaries and connection
  management.
- `server/registry/AGENTS.md` - **DEPRECATED** legacy registry (migration
  context only).
- `queryregistry/AGENTS.md` - canonical data-access translation layer.

---

## Read This First By Edit Type

- If editing a `*_module.py` file → read `server/modules/AGENTS.md` first.
- If editing under `server/modules/providers/` → read
  `server/modules/providers/AGENTS.md` first.
- If editing under `server/registry/` → read `server/registry/AGENTS.md` first
  (deprecation rules).
- If adding new data access operations → read `queryregistry/AGENTS.md` first.
