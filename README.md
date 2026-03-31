## TheOracleRPC

A modular business platform built on a typed RPC boundary. The platform
combines identity and role management, content pages/wiki CMS, user file
storage, finance operations (GL journals, ledgers, fiscal periods, billing
imports, reporting, credit lots), workflow automation, scheduled tasks,
Discord integration, AI generation (image, TTS, video), social distribution,
and LLM-agent access via TheOracleMCP.

Built on FastAPI, Azure SQL, and React. Deployed to Azure via GitHub Actions.
Connected to LLM agents via TheOracleMCP.

**Production:** https://elideusgroup.com
**Test:** https://elideus-group-test.azurewebsites.net
**Repository:** https://github.com/elide-us/elideus-group
**Patreon:** https://patreon.com/Elideus

### Tech Stack

| Layer | Technology |
|-------|------------|
| Runtime | Python 3.12, FastAPI, Uvicorn |
| Frontend | React, TypeScript, Vite |
| Database | Azure SQL (MSSQL), ODBC 18, aioodbc/pyodbc |
| Infrastructure | Azure Web App (Container/Linux), Azure Container Registry, GitHub Actions CI/CD |
| Authentication | OAuth 2.0/2.1 — Microsoft Entra, Google, Discord (Apple planned) |
| AI Services | OpenAI (chat completion, image generation, TTS), LumaAI (video generation) |
| Social | Discord bot, Bluesky bridge, TikTok (planned) |
| Agent Access | TheOracleMCP — Model Context Protocol server for LLM tooling |
| Storage | Azure Blob Storage (with provider abstraction for S3, CDN, local) |

### Core Features

- **Finance module** — double-entry accounting surface including ledgers,
  chart of accounts, journals and journal lines, number sequences, fiscal
  periods with 4-4-5 calendar generation, reporting (trial balance/journal
  summary/period status), vendors, payment requests, staging imports, and
  pipeline configuration.
- **Workflow automation** — database-driven workflow definitions and run
  actions with submit/cancel/rollback/resume/retry and stall scanning.
- **Scheduled tasks** — cron-style scheduled task definitions with history and
  manual `run_now` dispatch into workflows.
- **Content pages & wiki** — versioned page CMS and wiki content workflows
  with editable version history and route-aware page retrieval.
- **Products & commerce** — product catalog and user purchase flow with stub
  payment integration.
- **Renewals** — service renewal lifecycle management exposed via service RPC.
- **Conversation management** — system-level thread listing, stats, thread
  inspection, and cleanup operations for persona chat history.
- **RPC dispatch introspection** — reflection and rpcdispatch metadata layers
  for self-describing QueryRegistry/RPC topology and frontend tree views.
- **Template-driven image generation** — composable prompt templates with
  selectable style keys, tone, palette, lighting, composition, and subject
  parameters.
- **Text-to-speech** — voice synthesis via OpenAI TTS with configurable voice
  and model parameters.
- **Video generation** — LumaAI integration with callback-based async
  pipeline, automatic download and storage.
- **Creative workspace** — per-user file storage with upload, download,
  folder management, gallery publishing, and moderation queue.
- **Social distribution** — post generated content to Discord channels,
  Bluesky feeds, and TikTok (planned). Additional platforms (X, Meta) are
  medium-term targets.
- **Discord bot** — command-driven interface for chat summarization, persona
  conversations, and credit management (`!summarize`, `!persona`, `!credits`,
  `!guildcredits`).
- **TheOracleMCP** — LLM agents (Claude, Codex) connect via Model Context
  Protocol through `service.reflection` RPC operations for schema discovery,
  database introspection, and platform interaction.
- **Credit system** — credit lot lifecycle management (`create`, `consume`,
  `expire`, `list_events`, `wallet_balance`) plus legacy support/user credit
  reads.

### Architecture

TheOracleRPC follows a strict layered architecture with contract enforcement
at every boundary:

```
Clients / Input Surfaces
    ↓
RPC Layer (security gate — authentication, authorization, entitlements)
    ↓
Modules (application and business logic)
    ↓
Providers (storage, database, external APIs)
    ↓
Data Sources (structured responses back up the chain)
```

**Clients** are pure presentation layers with zero business logic — the React
frontend, Discord bot, TheOracleMCP, and any future input surface all send
typed RPC requests and render responses. See **INPUT_SHIMS.md**.

**RPC** is the typed public boundary. Every operation is URN-addressed
(`urn:domain:subsystem:operation:version`). The RPC layer validates bearer
tokens, checks role bitmasks, and enforces entitlements before dispatching.

**Modules** are the application. All business logic, workflow orchestration,
and decision-making lives here. Modules are loaded at startup by the
`ModuleManager` and communicate through well-defined interfaces.

**Providers** are the abstraction layer for external services. The same
interface can be implemented across platforms — Azure SQL vs PostgreSQL for
databases, Azure Blob vs S3 vs local disk for storage, OpenAI vs other LLMs
for chat completion. The database provider is the most complex because each
engine requires unique query syntax and system operations; the QueryRegistry
(`queryregistry/`) handles this translation. But the provider pattern applies
equally to storage, AI services, identity providers, and any other external
dependency.

See **ARCHITECTURE.md** for the full security model, role bit assignments, and
authentication workflows.

### Security

64-bit signed integer bitmask (63 usable bits) for role-based access control.
OAuth bearer tokens flow through every request. Anonymous access is limited to
`public.*` and `auth.*` RPC namespaces. All other namespaces require a valid
session and the appropriate role bits. See **ARCHITECTURE.md** for the role
table.

### Database

Azure SQL (MSSQL) is the production database provider. The QueryRegistry
architecture supports multiple providers; currently only MSSQL is implemented.

Conventions: `datetimeoffset(7)` with `SYSUTCDATETIME()` defaults for all
datetime columns, `bigint IDENTITY(1,1)` primary keys, ten canonical Extended
Data Types (EDTs), and a self-describing schema via the `reflection`
QueryRegistry domain. The EDT mapping table lives in the database itself,
seeded by deployment scripts, enabling future cross-provider support
(PostgreSQL, MySQL) without application code changes.

### Code Generation

RPC bindings and database namespace helpers are auto-generated from the Python
source:

- `python scripts/generate_rpc_bindings.py` — TypeScript RPC models and typed client accessors.
- `python scripts/generate_db_namespace.py` — TypeScript QueryRegistry namespace helpers.

Generated files are marked `DO NOT MODIFY - GENERATED`.

### Build & Deployment

All code changes are authored through Codex and deployed via GitHub Actions
CI/CD. The unified test harness validates the full stack:

```bash
python scripts/run_tests.py
```

This runs RPC binding generation, DB namespace generation, frontend
lint/type-check/test, and backend pytest in sequence.

Docker multi-stage build: builder stage runs generators and frontend build,
runtime stage copies artifacts and starts Uvicorn. See **BUILD.md**.

### AI Development Workflow

TheOracleRPC is built using Claude (architecture, planning, Codex prompt
generation) and Codex (code execution against the repository). All changes go
through human review. The MCP integration (TheOracleMCP) enables Claude to
introspect the live database schema and QueryRegistry structure during planning
sessions.

### Pull Request Testing

GitHub Actions run both Node and Python test suites on PRs targeting `main`.
Workflow: `.github/workflows/pr-tests.yml`.
