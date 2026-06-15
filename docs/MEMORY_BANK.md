# Agent Memory Bank

A persistent store of working context — decisions, invariants, specs, session
summaries, snippets — that an agent (e.g. Claude Code) can write and read across
sessions over MCP. It rides the existing MCP spine: the same gateway, identity,
authorization, and reflection machinery that backs the `oracle_*` tools.

- **Schema:** `migrations/v0.13.0.0_memory_foundation.sql`
- **Registration / wiring:** `migrations/v0.13.1.0_memory_seed.sql`
- **Host module:** `server/modules/memory_module.py` (`MemoryModule`, `app.state.memory`)
- **Tool wrappers + scopes:** `server/modules/mcp_io_service_module.py`

---

## Tool surface

All tools are exposed on the `mcp` gateway and dispatch to `MemoryModule`
methods. Writes use the non-read-only annotation; reads use the read-only one.

| MCP tool | Method | Scope | Args | Returns |
|---|---|---|---|---|
| `memory_store` | `store_memory` | `mcp:memory:write` | `project, kind, title, body, tags?, thread_guid?, source?` | `{ key_guid }` |
| `memory_update` | `update_memory` | `mcp:memory:write` | `key_guid, title?, body?, tags?, kind?, is_active?` | `{ key_guid }` |
| `memory_get` | `get_memory` | `mcp:memory:read` | `key_guid` | entry |
| `memory_search` | `search_memory` | `mcp:memory:read` | `query?, project?, kind?, tags?, limit=20, offset=0` | `{ entries[], total }` |
| `memory_list_recent` | `list_recent_memory` | `mcp:memory:read` | `project?, limit=20` | `{ entries[] }` |
| `memory_thread_create` | `create_thread` | `mcp:memory:write` | `project, title, summary?` | `{ key_guid }` |
| `memory_thread_get` | `get_thread` | `mcp:memory:read` | `thread_guid` | `{ thread, entries[] }` |

### Field conventions

- **`project`** — short slug grouping related memory, e.g. `flicker`,
  `oracle-unity`, `general`.
- **`kind`** — one of `decision | invariant | spec | note | session_summary |
  snippet`. (Not constrained by the DB in v1 — keep to this vocabulary.)
- **`title`** — one-line summary (≤256 chars).
- **`body`** — markdown detail.
- **`tags`** — optional space-delimited tags, e.g. `auth mcp schema`.
- **`source`** — optional provenance, e.g. `claude-code:<session-id>`.
- **`thread_guid`** — optional; attach an entry to a thread created with
  `memory_thread_create`.

`memory_update` is a partial patch: only the fields you pass change (COALESCE
preserves the rest) and `priv_modified_on` is bumped. `is_active=false`
soft-deletes (search/recent/thread reads exclude inactive rows; `memory_get`
still returns them). `limit` is clamped to 1–100.

---

## Authorization

Identity and authorization are unchanged from the rest of the MCP gateway
(see `McpIoServiceModule.resolve_identity` / `check_authorization`):

- **Static token (simplest path for Claude Code).** A bearer equal to the
  `MCP_AGENT_TOKEN` env var is granted the full static scope set, which now
  includes `mcp:memory:read` and `mcp:memory:write` alongside the existing
  `mcp:schema:*` / `mcp:data:*` / `mcp:rpc:*` / `mcp:admin` scopes.
- **Bearer JWT.** Session-issued or MCP-issued (`type=mcp_access`) tokens carry
  their scopes in claims; to use the memory tools a JWT must carry
  `mcp:memory:read` / `mcp:memory:write`.

Each binding declares `pub_required_scope`; a tool call succeeds only if the
identity's scope set contains it. No role or entitlement is required for memory.

---

## Table shapes

`dbo.agent_memory_threads` — optional grouping of related entries:

| column | type | notes |
|---|---|---|
| `key_guid` | `uniqueidentifier` | PK, `DEFAULT NEWID()` |
| `pub_project` | `nvarchar(128)` | not null |
| `pub_title` | `nvarchar(256)` | not null |
| `pub_summary` | `nvarchar(max)` | null |
| `pub_is_active` | `bit` | `DEFAULT 1` |
| `priv_created_on` / `priv_modified_on` | `datetimeoffset(7)` | `DEFAULT SYSUTCDATETIME()` |

`dbo.agent_memory_entries` — the memory records:

| column | type | notes |
|---|---|---|
| `key_guid` | `uniqueidentifier` | PK, `DEFAULT NEWID()` |
| `ref_thread_guid` | `uniqueidentifier` | null, FK → `agent_memory_threads.key_guid` |
| `pub_project` | `nvarchar(128)` | not null |
| `pub_kind` | `nvarchar(32)` | not null |
| `pub_title` | `nvarchar(256)` | not null |
| `pub_body` | `nvarchar(max)` | not null (markdown) |
| `pub_tags` | `nvarchar(512)` | null (space-delimited) |
| `pub_source` | `nvarchar(128)` | null |
| `pub_is_active` | `bit` | `DEFAULT 1` |
| `priv_created_on` / `priv_modified_on` | `datetimeoffset(7)` | `DEFAULT SYSUTCDATETIME()` |

Indexes: `IX_agent_memory_entries_project (pub_project, pub_is_active)`,
`IX_agent_memory_entries_kind (pub_kind)`,
`IX_agent_memory_entries_thread (ref_thread_guid)`.

Both tables are registered in the reflection catalog
(`system_objects_database_tables/_columns/_indexes/_constraints`), so the
`oracle_*` tools see them — `oracle_describe_table('agent_memory_entries')`
returns the schema above.

> **Timestamp note:** the original brief sketched `DATETIME2(7)`; the migration
> uses `DATETIMEOFFSET(7) DEFAULT SYSUTCDATETIME()` to match the repo-wide
> convention for `priv_*` audit columns and the reflection type registry
> (`system_objects_types` models `DATETIME_TZ` / `datetimeoffset(7)`, not
> `DATETIME2`).

---

## How a call flows

1. Claude calls `memory_search` over MCP with a bearer token.
2. The static wrapper in `_build_mcp()` calls `dispatch('memory_search', ctx, …)`.
3. `dispatch` looks up the binding (operation → method → `module_attr`),
   resolves identity from the bearer, checks `mcp:memory:read`, then calls
   `app.state.memory.search_memory(**kwargs)`.
4. `MemoryModule` runs the registered query `memory.entries.search` (loaded from
   `system_objects_queries` at startup) via `run_json_many` and returns
   `{ entries, total }`.

Adding a tool later = add a wrapper in `_build_mcp()`, a `MemoryModule` method,
and method/query/binding rows in a follow-up seed migration.

---

## Search: v1 and the upgrade path

**v1 (now):** `memory_search` does `LIKE`-based matching — `query` is matched
with `%term%` against `pub_title`, `pub_body`, and `pub_tags`; `project` and
`kind` are exact filters; `tags` is a `LIKE` filter. Results are ordered by
`priv_modified_on DESC`, paginated with `OFFSET/FETCH`, and `total` is the full
match count via `COUNT(*) OVER()`. This is intentionally simple and needs no
extra database objects.

**Upgrade path (not built yet):**

1. **Full-text.** Create a `FULLTEXT CATALOG` and a `FULLTEXT INDEX` over
   `(pub_title, pub_body, pub_tags)` and switch the `memory.entries.search`
   query to `CONTAINS` / `FREETEXT` with rank ordering. The tool surface and
   method signature stay the same — only the registered query text changes
   (plus a migration to create the catalog/index).
2. **Semantic / vector.** Add a `pub_embedding` column (e.g. `VARBINARY(MAX)` or
   a native vector type) populated by a local embedding model, and add a
   `memory.entries.search_semantic` query doing nearest-neighbour ranking. Expose
   it either as a new `mode` arg on `memory_search` or a sibling tool. Keep the
   `LIKE` path as the fallback.

Both upgrades are additive: new migration(s) + (optionally) a new registered
query, with no change to existing rows or the existing tool contract.
