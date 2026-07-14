# CLAUDE.md

Entry point for **Claude Code** working in this repo (TheOracleRPC / `elideus-group`).
Read this first, then the canonical docs under **Working in this repo** below.

> # ⭐ DO THIS FIRST — USE THE MEMORY SERVICE
> Your memory lives in **TheOracleMCP's memory service**: a dedicated, brand-new
> SQL memory surface built specifically for you, exposed via the **`memory_*`
> tools**. It is the source of truth for continuity across sessions.
>
> 1. **At the start of EVERY session, query it before anything else** —
>    `memory_search` / `memory_list_recent` for this project. Don't read other
>    docs, scan the repo, or ask the user to re-explain things until you've looked
>    here.
> 2. **As you work, write durable facts back to it** — `memory_store` (group a
>    workstream under a thread; see §2 for the tool surface).
> 3. **Prefer the memory service** over re-deriving context every session.
>
> This is the clean memory surface the maintainer built for you — **look at it and
> use it.** (If a `memory_*` call errors because the tool isn't loaded in this
> session, say so once and move on — do NOT loop searching for it.)

---

## 1. TheOracleMCP — live introspection (a claude.ai connector; usually ABSENT in Claude Code)

This project ships its own MCP server, **TheOracleMCP**, that exposes the live
test database and platform for introspection. **When the `oracle_*` tools are
actually in your tool list, prefer them over guessing about schema or data —
but in a Claude Code (CLI/IDE) session they usually are NOT there.** "Inspect the
live system" does NOT mean go hunting for a connection: it means check your tool
list *once*, and if the tools are absent, work offline (read the in-repo
SQL/migrations) without further probing or claiming to "connect."

> **⚠️ Surface check — read before reaching for `oracle_*` / `memory_*`.**
> These tools come from a **claude.ai custom connector**, NOT from this repo and
> NOT from any project MCP config. They are present in **claude.ai chat / Desktop**
> sessions that have the connector attached — and usually **absent in Claude Code
> (CLI/IDE) sessions** like this one. Do not go hunting for a project-level MCP
> setup; there isn't one.
>
> **If you need these tools, check your tool list exactly once** (they appear as
> `oracle_*` / `memory_*`, e.g. via a single ToolSearch). If they're not there,
> they're not coming this session — **stop searching, don't burn tokens re-probing,
> and don't claim to "connect."** Fall back to offline paths (read the SQL/migrations
> in-repo, run `pytest` / guardrails locally) and tell the user the live half needs
> the connector. To get them: (re)attach the connector to *this* surface, then start
> a **fresh session** so the tool list re-snapshots (see Gotcha below).

- **Endpoint:** `https://elideus-group-test.azurewebsites.net/mcp` (streamable HTTP)
- **Auth:** OAuth 2.1 via Microsoft Entra. On claude.ai it's a *custom connector*;
  the OAuth Client ID is a per-user static code the server maps to your identity
  (supply your own — do not commit it). The simplest programmatic path is a
  bearer equal to the `MCP_AGENT_TOKEN` env var, which carries the full static
  scope set (`mcp:schema:*`, `mcp:data:*`, `mcp:rpc:*`, `mcp:memory:*`, `mcp:admin`).
- **Tool families** (namespaced `mcp__<server>__…`):
  - `oracle_*` — schema/data reflection: `oracle_list_tables`, `oracle_describe_table`,
    `oracle_get_full_schema`, `oracle_list_views`, `oracle_dump_table`,
    `oracle_query_info_schema`, plus RPC-topology listers. These read the **live
    SQL Server catalog** (`sys.*` / `INFORMATION_SCHEMA`).
  - `memory_*` — the agent memory bank (see §2).
- **Gotcha:** a chat session snapshots the MCP tool list at session start. If the
  server gains tools mid-session, start a **fresh session** (or reconnect the
  connector) to see them.

## 2. Agent memory bank — maintain continuity across sessions & projects

The memory bank is how we keep continuity between sessions and across projects.
**Full reference: [`docs/MEMORY_BANK.md`](docs/MEMORY_BANK.md).** The loop:

1. **At session start, query the memory service FIRST** — `memory_search(query=…)`
   and/or `memory_list_recent(project=…)` for the project you're working on, before
   reading other docs or re-deriving context.
2. **While working** — record durable facts: `memory_store(...)`. Group a
   workstream under a thread (`memory_thread_create` → pass its `key_guid` as
   `thread_guid`); read it back with `memory_thread_get`.
3. **Patch / retire** — `memory_update(key_guid, …)`; `is_active=false`
   soft-deletes.

| Tool | Scope | Key args |
|---|---|---|
| `memory_store` | `mcp:memory:write` | `project, kind, title, body, tags?, thread_guid?, source?` → `{key_guid}` |
| `memory_search` | `mcp:memory:read` | `query?, project?, kind?, tags?, limit, offset` → `{entries[], total}` |
| `memory_list_recent` | `mcp:memory:read` | `project?, limit` → `{entries[]}` |
| `memory_get` | `mcp:memory:read` | `key_guid` → entry |
| `memory_update` | `mcp:memory:write` | `key_guid, title?, body?, tags?, kind?, is_active?` |
| `memory_thread_create` | `mcp:memory:write` | `project, title, summary?` → `{key_guid}` |
| `memory_thread_get` | `mcp:memory:read` | `thread_guid` → `{thread, entries[]}` |

- **`project`** is a short slug (e.g. `elideus-group`, `general`). Use one slug
  per body of work so a future session can find it.
- **`kind`** ∈ `decision | invariant | spec | note | session_summary | snippet`.
- Don't hardcode thread GUIDs anywhere durable — **search the bank** for the
  active thread under your project slug instead.

---

## 3. Working in this repo

**Orientation docs (canonical — defer to these):**
- [`AGENTS.md`](AGENTS.md) — repo-wide ground rules; obey the most specific
  scoped `AGENTS.md` covering files you touch.
- `PATTERNS.md` — layer architecture, RPC dispatch, module lifecycle,
  QueryRegistry, codegen, and the MCP tooling reference (§7).
- [`README.md`](README.md) — what the platform is and its tech stack.

**Git / deploy workflow — the branch model (commit it to memory, do NOT re-derive):**
- **`macbook` = the maintainer's LOCAL working branch** (on the MacBook). All
  local work and commits land here. This is just where code is written; it is
  NOT a deploy target.
- **`test` = the branch on GitHub.** The maintainer opens PRs `macbook` → `test`;
  merging to `test` is what auto-deploys to the test site. **`test` is the
  remote/deploy branch.**
- Therefore: a commit sitting on `macbook` / `origin/macbook` but not yet on
  `test` is **normal and expected** — it just means the maintainer hasn't PR'd it
  yet. Do **NOT** read that as "unfinished," "not deployed = broken," or anything
  that needs flagging. Deploy timing is the maintainer's call, not a status you
  infer or report unless explicitly asked.
- **Do not run git operations** (branch/commit/merge/push) and **do not open
  PRs** unless explicitly asked — the maintainer owns the `macbook` → `test` PR
  flow.

**Database changes:**
- Deliver schema/data changes as `migrations/*.sql` for the maintainer to run
  via **SSMS** (no auto-runner). Modules read the DB only at **startup**, so the
  sequence is: apply migration → redeploy/restart → verify with `oracle_*`.
- `db.run(...)` is allowed **only** under `server/modules/providers/`; everywhere
  else use registered queries via `queryregistry.providers.mssql`
  (`run_json_one/many`, `run_exec`). Enforced by
  `scripts/check_db_run_boundaries.py`.

**Tests / checks:**
- Full harness: `python scripts/run_tests.py` (codegen + frontend lint/type/test + pytest).
- Quick backend: `pytest` from `tests/`.
- Guardrail: `python scripts/check_db_run_boundaries.py`.

**Conventions:** Python = 2-space indent; TypeScript = 4-space; datetime columns
= `datetimeoffset(7)` default `SYSUTCDATETIME()`; deterministic registration
GUIDs are `uuid5` (see `PATTERNS.md`). Update tests + docs alongside code.
