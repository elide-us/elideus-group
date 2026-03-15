## TheOracleRPC

AI-powered content generation platform. Template-driven image generation,
text-to-speech, video generation, social media distribution, and creative
workspace management — all behind a typed RPC boundary with OAuth
authentication and role-based access control.

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

- **Template-driven image generation** — composable prompt templates with
  selectable style keys, tone, palette, lighting, composition, and subject
  parameters. Templates are stored server-side; the frontend is a selector
  over server-provided options.
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
  conversations, user registration, and credit management.
- **TheOracleMCP** — LLM agents (Claude, Codex) connect via Model Context
  Protocol for schema discovery, database introspection, and platform
  interaction.
- **Credit system** — per-user credit tracking with charge-per-operation for
  AI service calls.

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
