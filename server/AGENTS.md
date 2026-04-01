# Server AGENT Instructions

This file covers the FastAPI application entry point, startup sequence, and
other top-level server concerns.

---

## Layering Expectations

- Follow **PATTERNS.md** for layer architecture, dispatch patterns, and data conventions.
- Layer responsibilities: Modules (business logic) → QueryRegistry
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

## Layer-Specific Guidance

- `server/modules/AGENTS.md` - module lifecycle and business logic patterns.
- `server/modules/providers/AGENTS.md` - provider boundaries and connection
  management.
- `queryregistry/AGENTS.md` - canonical data-access translation layer.

---

## Read This First By Edit Type

- If editing a `*_module.py` file → read `server/modules/AGENTS.md` first.
- If editing under `server/modules/providers/` → read
  `server/modules/providers/AGENTS.md` first.
- If adding new data access operations → read `queryregistry/AGENTS.md` first.
