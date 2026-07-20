# CLAUDE.md — elideus-group (TheOracleRPC / TheOracleMCP, v2.5)

**The MCP memory server is the single source of truth for this project.** The durable
architecture, standards, specs, decisions, and the branch/deploy model live there as
linked entries. Any remaining local `.md` docs are being migrated into MCP and retired —
do not add new ones, and where a doc conflicts with MCP, MCP wins.

- **Read MCP first — every session, every task.** Use `memory_list_recent`,
  `memory_search`, `memory_coderules`, and `memory_get` for project `elideus-group`, plus
  the universal `general` rules (and `elideus-group-unity` for the v3 / ETG architecture).
  "Where's the spec / rule / doc for X?" resolves to an MCP entry, never a file.
- **The `memory_*` / `oracle_*` tools ARE available here** — TheOracleMCP is a connector that
  works in Claude Code, not just claude.ai chat. **If they are NOT in your tool list, the
  memory is unavailable — DO NOT PROCEED:** state that the connector needs (re)attaching and
  a fresh session (the tool list is snapshotted at session start), then stop and wait. Do not
  fall back to files or reconstruct context from the repo.
- **Before creating any file, module, or query:** grep the repo *and* query
  `memory_coderules` + `memory_search`; if either surfaces a match, extend it in place —
  never write a parallel implementation.
- **Store durable knowledge only in MCP** (`memory_store` + `memory_link_add` — linked
  entries, not prose). Never write a `docs/*.md` or any local `.md` design/memory file.

This repo is the **v2.5** architecture of TheOracleMCP (legacy, running in prod); the **v3 /
ETG** rebuild lives in `elideus-group-unity`. Start from the MCP entry _"elideus-group =
TheOracleMCP v2.5 architecture …"_ and walk its links.
