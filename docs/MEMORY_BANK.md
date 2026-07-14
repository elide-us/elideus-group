# Agent Memory Bank

A persistent store of working context — decisions, invariants, specs, session
summaries, snippets — that an agent (e.g. Claude Code) can write and read across
sessions over MCP. It rides the existing MCP spine: the same gateway, identity,
authorization, and reflection machinery that backs the `oracle_*` tools.

- **Schema:** `migrations/v0.13.0.0_memory_foundation.sql`
- **Registration / wiring:** `migrations/v0.13.1.0_memory_seed.sql`
- **Confidence + contradictions:** `migrations/v0.13.2.0_memory_confidence.sql`
  (FDD-ORACLE-MEM-CONFLICT-01, Phase 1 — see [Confidence-weighted memory](#confidence-weighted-memory-v01320) below)
- **Host module:** `server/modules/memory_module.py` (`MemoryModule`, `app.state.memory`)
- **Tool wrappers + scopes:** `server/modules/mcp_io_service_module.py`

---

## Tool surface

All tools are exposed on the `mcp` gateway and dispatch to `MemoryModule`
methods. Writes use the non-read-only annotation; reads use the read-only one.

| MCP tool | Method | Scope | Args | Returns |
|---|---|---|---|---|
| `memory_store` | `store_memory` | `mcp:memory:write` | `project, kind, title, body, tags?, thread_guid?, source?, confidence?, confidence_source?` | `{ key_guid }` |
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
- **`confidence`** — optional 0..1 scalar. **Confidence, not truth** — omit it
  to take the per-kind base weight (or 1.0 when `confidence_source='human'`).
  Clamped to `[0, 1]`.
- **`confidence_source`** — optional `agent | human | derived | imported`
  (default `agent`). A `human` source pins confidence to 1.0 as a *source*
  property; that is still not truth (a human can typo).

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
| `pub_confidence` | `decimal(19,5)` | `DEFAULT 0.70` — 0..1 confidence (v0.13.2.0) |
| `pub_confidence_source` | `nvarchar(32)` | `DEFAULT 'agent'` — agent\|human\|derived\|imported |
| `pub_node_state` | `nvarchar(24)` | `DEFAULT 'active'` — active\|conflict\|historical\|retired |
| `pub_ref_count` | `int` | `DEFAULT 0` — inbound-authority count (Phase 2 maintains) |
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

## Confidence-weighted memory (v0.13.2.0)

Implements **FDD-ORACLE-MEM-CONFLICT-01, Phase 1**. The governing principle:

> **Weight is confidence, not truth.** Confidence gates how loudly the system
> objects to a contradiction — never whether a claim is correct. A high-confidence
> claim can be wrong; a human statement is `1.0` as a *source* property, and a
> human can still typo. No write path silently overwrites a claim that has inbound
> references.

### Claim attributes (on `agent_memory_entries`)

- **`pub_confidence`** `0..1` — set explicitly, or defaulted from the per-kind
  policy below. Clamped in `MemoryModule._resolve_confidence`.
- **`pub_confidence_source`** — `agent | human | derived | imported`. `human`
  pins confidence to `1.0`.
- **`pub_node_state`** — `active | conflict | historical | retired`. A node in
  `conflict` has an open contradiction record. State is persistent and queryable,
  not a transient exception.
- **`pub_ref_count`** — materialised inbound-authority count (Phase 2 maintains).

### Initial weighting (per-kind base confidence)

Applied by the caller at insert time and mirrored by the migration's PHASE 2
backfill of pre-existing rows. Single logical policy — the numbers live in
`_BASE_CONFIDENCE` (`memory_module.py`) and the migration; keep them in sync.

| kind | base confidence |  | kind | base confidence |
|---|---|---|---|---|
| `invariant` | 0.90 |  | `snippet` | 0.70 |
| `decision` | 0.85 |  | `note` | 0.60 |
| `spec` | 0.80 |  | `session_summary` | 0.55 |
| `reference` | 0.75 |  | *(unlisted)* | 0.70 |

### `agent_memory_references` — the mind-map edges

`ref_from_guid --(pub_ref_kind, pub_weight)--> ref_to_guid`, both FK →
`agent_memory_entries.key_guid`. `pub_ref_kind` ∈ `cites | supports | supersedes
| derived_from | contradicts | disambiguates`. Inbound active `cites`/`supports`
edges are what confer authority — that authority *is* the confidence signal, made
explicit. Unique on `(ref_from_guid, ref_to_guid, pub_ref_kind)`.

### `agent_memory_contradictions` — first-class conflict records

When a new claim challenges an existing one, the system **records the conflict**
rather than resolving it — both claims persist; neither is destroyed:

| column | notes |
|---|---|
| `ref_claim_a_guid` / `ref_claim_b_guid` | the two competing entries (FK → entries) |
| `pub_state` | `open \| resolved` — the conflict lifecycle |
| `pub_resolution` | on resolve: `correction \| new_version \| typo \| contradiction \| misunderstanding` |
| `pub_resolution_note` / `pub_resolved_source` | how it was resolved, and by whom (human authority) |

Resolution is an **explicit, classified transition** (FDD §4), never an implicit
side effect of a write. `IX_agent_memory_contradictions_state` is the
"interrupt the human" queue (open conflicts, by project).

### Phase 1 vs Phase 2

Phase 1 (this migration) is **schema + weighting foundation**: the columns and
both tables exist and `memory_store` accepts `confidence`, but the reference and
contradiction tables have no write/read tooling yet, so they start empty. **Phase
2** wires the behaviour — proposed tools: `memory_link_add`,
`memory_conflict_open`, `memory_conflict_resolve`, `memory_conflicts_list`, plus
`pub_ref_count` recompute. Those are additive (new methods/queries/bindings on the
existing `mcp:memory:*` scopes — no OAuth change), following the same
wrapper→dispatch→binding→method→query pattern as the existing tools.

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
