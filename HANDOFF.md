# Handoff — Agent Memory Bank (elideus-group)

> Scratch handoff for continuing in a fresh session. Safe to delete once Phase 4 lands.
> Start the new session, then say: **"Read HANDOFF.md and continue."**

## TL;DR / next action

Phases 1–3 (the MCP memory bank) are **built, applied to the live test DB, and code-deployed**. The only reason the previous session couldn't call the `memory_*` tools is that a chat session snapshots an MCP server's tool list **once at session start** — that session began before the tools existed. **A fresh session will see all 21 tools (14 `oracle_*` + 7 `memory_*`).**

So, in the new session:
1. Run the **live verification checklist** below (call the real `memory_*` tools).
2. If green, do **Phase 4** (prune the web app to the MCP spine) — scripts only, for the user to run. Mind the two traps.

The user manages git/deploys themselves — **do not touch git** unless asked. The user dislikes over-verification: keep tool calls minimal and to the point; don't "build an airplane every prompt." Don't run broad filesystem scans.

---

## What exists (Phases 1–3 + docs) — all DONE & verified on the live DB

Files (working tree on branch `macbook`, which == `origin/test`):
- `migrations/v0.13.0.0_memory_foundation.sql` — `agent_memory_threads` + `agent_memory_entries` + 3 indexes + FK + reflection registration. **Applied.**
- `migrations/v0.13.1.0_memory_seed.sql` — module + 7 methods + 7 `memory.*` queries + 7 `memory_*` MCP bindings. **Applied.**
- `server/modules/memory_module.py` — `MemoryModule` (`app.state.memory`), 7 typed methods over registered queries. **Deployed.**
- `server/modules/mcp_io_service_module.py` — `_WRITE_ANNOTATIONS`, 7 tool wrappers, `mcp:memory:read`/`mcp:memory:write` added to the static-token scope set. **Deployed.**
- `docs/MEMORY_BANK.md` — tool surface, scopes, table shapes, search upgrade path.

Verified read-only via the live `oracle_*` tools (last session):
- `oracle_describe_table('agent_memory_entries')` → 11 cols, 3 indexes, FK → `agent_memory_threads` ✅
- `system_objects_modules` has `MemoryModule` (`pub_state_attr=memory`) ✅
- 41 gateway bindings (was 34): all 7 `memory_*` on the mcp gateway with correct scopes/read-only flags; all 14 `oracle_*` intact ✅

Two deliberate deviations from the original brief (documented in migration headers):
1. Timestamps are `DATETIMEOFFSET(7)` not `DATETIME2(7)` — matches every existing `priv_*` column and the reflection type registry (no DATETIME2 EDT exists).
2. Reflection index/constraint rows use deterministic UUID5 GUIDs (brief's existing rows used `NEWID()`) so the migration is re-runnable.

Local dev: `.venv` exists (gitignored) with `requirements.txt` + `requirements-dev.txt` installed. `pytest` passes; `python scripts/check_db_run_boundaries.py` passes (memory module uses `run_json_*` directly, which is allowed).

---

## STEP 1 — Live verification checklist (run these tools)

Use the `mcp__<server>__memory_*` tools (the static `MCP_AGENT_TOKEN` path already grants the new scopes). Suggested run:

1. `memory_store(project="general", kind="note", title="handoff smoke test", body="verifying memory bank end to end", tags="smoke handoff")` → expect `{ key_guid }`.
2. `memory_search(query="handoff")` → expect the entry, `total >= 1`.
3. `memory_get(key_guid=<from step 1>)` → expect the full entry.
4. `memory_list_recent(project="general")` → expect the entry near the top.
5. `memory_thread_create(project="general", title="handoff thread")` → `{ key_guid }`; then `memory_store(..., thread_guid=<that>)`; then `memory_thread_get(thread_guid=<that>)` → expect `{ thread, entries[] }` round-trip.
6. `memory_update(key_guid=<step 1>, tags="smoke handoff done")` → `{ key_guid }`; confirm via `memory_get`.
7. Sanity: an `oracle_*` call still returns normally.

If a memory tool returns "Memory query not loaded…", the module started before the seed migration — the module just needs a restart (it loads queries at startup).

---

## STEP 2 — Phase 4: prune to the MCP spine (LAST; deliver scripts only)

Goal: drop the web app + ContentForge, keep the MCP + auth + reflection spine + the new memory layer. **Reversible order: deactivate → verify → delete → drop.** Deliver as `scripts/prune/*.sql` for the **user to run manually** (never execute SQL yourself). Each script gets a header: what it removes + that it's irreversible.

### Gateways (from live `system_objects_io_gateways`)
- `mcp`  = `1287363D-8093-564A-A8CA-D0AE6985BDBD` (host `mcp_io`) — **KEEP**. Hosts `oracle_*` (→ `rpcdispatch`) + new `memory_*` (→ `memory`).
- `rpc`  = `606C04E3-44F1-593D-9C8B-8006E0A377D3` (host `rpc_io`) — **PRUNE**. All `urn:*` web ops (20 bindings).
- `api`  = `37C5B8BD-698F-5182-82B9-33BC3FE4CD4D` (host `rpc_io`) — future REST, no bindings. Prune with rpc_io.
- `discord` = `16825F1A-EF4B-55DB-8D5A-898A5DFB69B1` (host `discord_io`) — optional keep (write-log channel).

### ⚠️ Two traps in the original brief's drop list — these MUST be KEPT
1. **`rpcdispatch_module`** — hosts all 14 `oracle_*` reflection methods on the mcp gateway (verified: every mcp binding's `ref_method_guid` is an `RpcdispatchModule` method, GUID `F13CB430-…`). Do **not** drop.
2. **`system_objects_types`** — the shared EDT type registry that `oracle_describe_table`/`get_full_schema` JOIN for `pub_mssql_type` (and that the memory reflection rows reference). Not a ContentForge table. Dropping it breaks reflection. **Keep.**

### Drop set (verify no keep-set dep first)
- Code dirs: `frontend/`, `client/`, `static/`, `pagespec/`.
- Web/ContentForge modules: `service_routes_module`, `cms_workbench_module`, `contract_query_builder_module`, `public_vars_module`, `rpc_io_service_module`. (NOT `rpcdispatch_module`, NOT `database_cli_module` until traced.)
- DB tables (FK-safe order, from the brief, MINUS `system_objects_types`): `system_objects_components`, `system_objects_component_tree`, `system_objects_pages`, `system_objects_page_data_bindings`, `system_objects_tree_categories`, `system_objects_tree_subcategories`, `system_objects_tree_category_tables`, `system_objects_type_controls`, `system_objects_routes`. **Re-verify each against the live FK graph (`oracle_describe_table`) before writing the DROP order.**

### Suggested deliverables
- `scripts/prune/01_deactivate_web_gateway.sql` — `UPDATE … SET pub_is_active=0` for rpc/api gateway `urn:*` bindings + gateway + web module rows. (Reversible.)
- `scripts/prune/02_delete_web_registry.sql` — `DELETE FROM …` those rows, after verification.
- `scripts/prune/03_drop_contentforge_tables.sql` — `DROP TABLE …` ContentForge tables in FK-safe order.
Keep every code commit bootable; sequence so memory + reflection still work after each step.

---

## Key reference (so you don't re-derive)

Persistent memory files (auto-loaded; read them): `memory-bank-project`, `elideus-group-mcp-conventions`, `dont-scan-whole-filesystem` (indexed in the project's `MEMORY.md`). The conventions memory has the UUID5 scheme, dispatch path, reflection tables, EDT type GUIDs, and gotchas (incl. the `mcp_io` vs `mcp_io_service` app.state-attr quirk).

Live read-only inspection: the connected `oracle_*` MCP tools query the test DB — use them instead of guessing. Migrations are applied externally (no auto-runner); modules read the DB only at startup, so apply-migration → redeploy/restart.
