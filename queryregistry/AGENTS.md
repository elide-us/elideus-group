# Query Registry AGENT Instructions (Canonical)

`queryregistry/` is the **canonical query registry** and the target destination for all
new registry work. `server/registry/` is legacy and being deleted domain-by-domain.
Do not add new code to `server/registry/`.

---

## What this layer IS

- A provider abstraction and **data access translation layer** for canonical DB operations.
- A translation boundary that accepts typed requests from modules, maps canonical
  operation names to provider-specific SQL handlers, and returns typed responses.
- Domain/subdomain operation routing using canonical operation names:
  `db:domain:subdomain:operation:version`
- A layer with **zero business logic**.

## What this layer is NOT

- Not a compatibility wrapper for legacy naming schemes.
- Not a place to add aliases/fallback shims to legacy `server/registry` operations.
- Not a module/provider lifecycle layer (see `server/modules/AGENTS.md`).
- Not a place for business logic, conditional workflows, or application rules;
  those belong in `server/modules/`.

---

## Core files and dispatch flow

- `queryregistry/models.py` – canonical `DBRequest` / `DBResponse` contracts.
- `queryregistry/helpers.py` – operation parsing helpers.
- `queryregistry/dispatch.py` – top-level domain dispatch map.
- `queryregistry/<domain>/handler.py` – domain-level subdomain dispatch.
- `queryregistry/system/dispatch.py` – shared `SubdomainDispatcher` protocol.
- `queryregistry/stubs.py` – CRUD stub dispatcher generator for greenfield domains.

Dispatch pattern:
1. Parse `db_request.op` with `parse_query_operation`.
2. Route by domain in `queryregistry/dispatch.py`.
3. Route by subdomain in domain `handler.py`.
4. Route operation/version inside subdomain handlers (often via dispatch map keys such as
   `("create", "1")`, `("read", "1")`, etc.).

---

## SubdomainDispatcher usage

- Reuse `SubdomainDispatcher` from `queryregistry/system/dispatch.py` where protocol typing is needed.
- Do not redefine local Protocol variants for equivalent dispatcher signatures.
- Keep dispatcher call signature consistent:
  `async def __call__(request: DBRequest, *, provider: str) -> DBResponse`.

---

## Typed contract pattern

- Define typed payload models in subdomain `models.py` when a domain needs structured inputs.
- Convert incoming `request.payload` into typed params before provider-specific
  data access calls.
- Return canonical `DBResponse` objects (or provider-normalizable equivalents) with explicit
  payload/rowcount behavior.

---

## Adding a new domain or subdomain

1. Add domain package and `handler.py`.
2. Register domain handler in `queryregistry/dispatch.py`.
3. Add subdomain package with:
   - `handler.py` (subdomain routing)
   - `models.py` (typed payload contracts, when needed)
   - `services.py` for translation/data-access helpers only (no business rules)
   - `mssql.py` (or provider-specific adapters) for SQL execution paths
4. Wire operation/version dispatch maps using canonical op fragments.
5. Ensure callers use canonical `db:domain:subdomain:operation:version` names.

---

## CRUD stub structure

- For new-but-not-implemented paths, use `queryregistry/stubs.py` to expose consistent
  `create/read/update/delete/list` + version dispatcher entries.
- Stub responses should fail explicitly (e.g., HTTP 501) rather than silently aliasing to
  unrelated handlers.

---

## Naming and schema conventions

- Maintain DB metadata naming conventions in payloads/results:
  - `element_*` fields.
  - `recid` as `bigint` IDs.
  - `datetimeoffset` for temporal metadata.

---

## Anti-patterns (forbidden)

- Alias maps that translate new operation names back to legacy names.
- New fallbacks to `server/registry/` for greenfield features.
- Business logic, conditional workflows, or application rule enforcement.
- Mixing module lifecycle concerns into query handlers.

Adjacent guidance:
- `server/modules/AGENTS.md`
- `server/modules/providers/AGENTS.md`
- `server/registry/AGENTS.md` (legacy/deprecation-only context)
