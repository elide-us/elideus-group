# AGENT Instructions

This document provides instructions and background context for the Codex CLI code agent. It explains how to interact with the project’s build, test, and deployment workflows, as well as how to respect the layered security model.

---

## Automation and Scripting

The repository includes several scripts to automate builds, testing, and database management.
These are the *canonical entry points* for automation and must be used to model workflows correctly.

* **`dev.cmd`**
  Provides different build workflows. Use this to model required build and test actions on Windows.

* **`run_tests.py`**
  Centralized entry point for running tests. Always use this when modeling test workflows.

* **`mssql_cli.py`** and **`msdblib.py`**
  Contain functions for SQL Server schema and data management. Use these utilities for schema dumps, migrations, and maintenance tasks.

* **Docker considerations**
  The Dockerfile and `buildx` process may be affected by changes, but there is no automated test coverage for these steps. Exercise caution when modifying anything related to container builds.

---

## Coding Standards

* Python scripts use **2-space indentation**.
* TypeScript files use **4-space tabs**.
* All tests, scripts, and documentation must be updated alongside code changes.
* Linting and type-checking are required for the frontend (`npm lint`, `npm type-check`).

---

## Database Management

* Schema files are tracked in `/scripts`. When schema changes are required, generate a new version using the `schema dump` process from `mssql_cli.py`.
* When data loads are needed, prefer a `.sql` script. Human developers will run the import using `mssql_cli.py`.

---

## Testing Details

* Always regenerate RPC bindings before running tests.
* Frontend: run `npm lint`, `npm type-check`, `npm test`.
* Backend: run `pytest` against the `/tests` folder.

---

## React Styling

* All React components should use **ElideusTheme** for consistent styling.
* Update `theme.d.ts` when adding or modifying theme variants.

---

## Tech Stack

The project currently uses:

* **Node 18 / React / TypeScript** → Frontend web app
* **FastAPI on Python 3.12** → Backend RPC server
* **Docker** → WSGI-compliant containerization

---

## Module Initialization

The **server module system** uses a **two-phase initialization pattern** to ensure clean startup ordering and dependency handling.

### Phase 1 — Instantiation

* `server/modules/__init__.py` auto-loads every file ending in `_module.py`.
* Each class is instantiated immediately and attached to `app.state` using the filename without the suffix.

  * Example: `db_module.py` → available as `app.state.db`.
* At this stage, all module objects exist and can be referenced, but **none are “ready” yet**.

### Phase 2 — Asynchronous Startup

* Once all modules are instantiated, the system calls each module’s `startup()` coroutine.
* Within `startup()`, a module may:

  * Fetch other modules from `app.state`.
  * Await their `on_ready()` to guarantee dependencies are initialized.
  * Perform its own setup work.
* When initialization completes, the module calls `mark_ready()`.
* This signals all awaiting modules that the dependency is now safe to use.

### Ordering Behavior

* Modules with no dependencies complete their startup immediately and mark themselves ready.
* Modules that depend on others will yield until their dependencies signal readiness.
* This creates a **natural dependency graph**: startup order emerges automatically without explicit sequencing.

### Contract

* **Every module must inherit from `BaseModule`**.
* Call `super().__init__(app)` in the constructor.
* Consumers of a module must always `await on_ready()` before use.
* Modules may optionally expose helpers on `app.state` for use by others.

This design ensures that startup is deterministic, deadlock-free, and extensible: modules only proceed when their dependencies are explicitly ready.



## File Structure

### Python

* `/` → build automation, configuration, main FastAPI entrypoint
* `server/` → FastAPI server, modules, routes, helpers
* `rpc/` → Pydantic models, RPC handlers, services

### React

* `frontend/` → React/TypeScript web app, compiled into `/static`

### Special

* `tests/` → Unit and process tests
* `scripts/` → RPC-to-TS generation, schema, automation

---

# Security Model

This section defines the layered security domains. It describes how authentication, identity, and authorization are separated and enforced.

---

## 1. Identity Providers (External)

* Providers: Microsoft, Google, Apple, Discord
* Only source of authentication — no local credentials exist.
* Tokens are issued to the client (via MSAL or equivalent).
* Server responsibility: validate tokens, extract claims.
* Server non-responsibility: managing or refreshing provider tokens.

---

## 2. Internal User Domain

* On first login, the system creates a **unique GUID** for the user.
* The GUID is the sole server-side identity key.
* All tracked state (sessions, devices, credits, entitlements, profile image) is keyed to the GUID.
* User profile data is minimal and opt-in.

---

## 3. Client Application Domain

* The React frontend is user-owned.
* May store provider tokens and private user data.
* Receives server-issued bearer tokens (encrypted with GUID).
* The server cannot reach into client storage; the client only gets what it needs for RPC.

---

## 4. Server Authentication Domain

* Anonymous requests (no token) → access limited to `public.*` and `auth.*` RPC domains.
* Login flow:

  1. Validate provider token
  2. New user → create GUID, seed 50 credits, assign base role
  3. Existing user → load state, refresh session/device
  4. Issue bearer token with GUID
  5. Return profile + token to client

---

## 5. RPC Security

* Every RPC call must include a server-issued bearer token.
* Request flow:

  * Decrypt token → extract GUID
  * Build `RPCRequest` (GUID + operation URN)
  * Check security (roles, credits, entitlements)
  * Allow or deny, then return `RPCResponse`

---

## 6. Separation of Concerns

* Identity providers → manage identity & tokens
* Client → stores provider tokens, private data
* Server → enforces security via GUID + bearer tokens
* Internal roles/entitlements never leak to client

---

## 7. Workflow Summary
```
flowchart TD
    A[Client] -->|Provider Token| B[Server: Validate]
    B -->|New User| C[Create GUID + Credits]
    B -->|Existing User| D[Load State]
    C --> E[Generate Bearer Token (GUID inside)]
    D --> E[Generate Bearer Token (GUID inside)]
    E -->|Bearer Token| A
    A -->|RPCRequest + Bearer| F[RPC Layer]
    F -->|Check Security (GUID)| G[Authorized?]
    G -->|Yes| H[Dispatch Operation]
    G -->|No| I[Return Denial]
    H --> J[RPCResponse]
    I --> J
    J --> A
```

## 8. Key Principles

* Do not bypass or merge domains.
* Do not expose security details.
* Always key state off GUID.
* Respect boundaries: provider (external), client (user-owned), server (enforced).

## 9. Additional Documentation

When required, refer to the following documents for additional details:

- DATABASE.md - Contains details about the database schema and design concepts
- RPC.md - Outlines the RPC namespace and associated security paradigms
- SECURITY.md - Details the security model and how roles are used in the system

