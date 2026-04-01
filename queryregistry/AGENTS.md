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

## MSSQL query standards

The default database provider is Microsoft SQL Server (enterprise). The query
registry supports MySQL and PostgreSQL, but MSSQL is the primary target and has
specific requirements that every `mssql.py` implementation must follow.

### SET NOCOUNT ON

**Every multi-statement SQL string that uses INSERT/UPDATE/DELETE followed by a
SELECT must begin with `SET NOCOUNT ON;`.** Without it, pyodbc consumes the
intermediate rowcount result from the DML statement and never advances to the
trailing SELECT. This causes `No results. Previous SQL was not a query.` errors
at runtime.

This applies to:
- `OUTPUT ... INTO @table_variable` followed by `SELECT * FROM @table_variable`
- `UPDATE ... SET ...` followed by a `SELECT` in the same batch
- Any `INSERT`/`UPDATE`/`DELETE` combined with a trailing `SELECT ... FOR JSON`

Simple single-statement queries (a lone `SELECT ... FOR JSON`) do not need it.
`run_exec` calls (fire-and-forget DML with no result) should still use
`SET NOCOUNT ON;` to suppress unneeded rowcount messages.

Example pattern:
```sql
SET NOCOUNT ON;
DECLARE @inserted TABLE (...);

INSERT INTO my_table (...)
OUTPUT inserted.* INTO @inserted
VALUES (...);

SELECT * FROM @inserted FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
```

### FOR JSON output

- Single-row results: `FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES`
- Multi-row results: `FOR JSON PATH, INCLUDE_NULL_VALUES`
- Always include `INCLUDE_NULL_VALUES` so null columns appear in JSON output.

### Parameterized queries

- Use `?` positional placeholders (pyodbc ODBC style), not named parameters.
- Use `TRY_CAST(? AS DATETIMEOFFSET(7))` for datetime parameters.
- Use `TRY_CAST(? AS UNIQUEIDENTIFIER)` for GUID parameters.
- Never interpolate values into SQL strings.

### Dynamic UPDATE builders

When building UPDATE statements dynamically (e.g., only setting changed
fields), always include `SET NOCOUNT ON;` at the top of the SQL template and
`element_modified_on = SYSUTCDATETIME()` in the SET clause.


Adjacent guidance:
- `server/modules/AGENTS.md`
- `server/modules/providers/AGENTS.md`
