# AGENT Instructions

This document provides concise rules and operational guidance for the Codex CLI code agent. It is focused on coding agent rules; detailed architectural and security design is documented separately in **ARCHITECTURE.md**.

---

## Automation and Scripting

* **`dev.cmd`** – Use for build/test actions on Windows.
* **`run_tests.py`** – Canonical entry point for running tests.
* **`mssql_cli.py`** and **`scriptlib.py`** – Utilities for schema migrations and maintenance tasks.
* **Docker builds** – No automated test coverage; modify with caution.

---

## Coding Standards

* Python → 2-space indentation.
* TypeScript → 4-space tabs.
* Update tests, scripts, and docs with code changes.
* Run `npm lint` and `npm type-check` for frontend.

---

## Database Management

* For data loads, generate a `.sql` file. Human developers will import manually using **SSMS**.

---

## Testing Details

* Always regenerate RPC bindings before running tests.
* Frontend: `npm lint`, `npm type-check`, `npm test`.
* Backend: `pytest` in `/tests`.

---

## Tech Stack

* **Node 18 / React / TypeScript** – Frontend.
* **FastAPI (Python 3.12)** – Backend RPC server.
* **Docker** – Containerization.

---

## Module and Provider Rules

* **Modules** = business logic. Implement modules when new functionality is required.
* **Providers** = interchangeable backends. Implement when multiple providers are possible (e.g., Azure vs. AWS, MSSQL vs. Postgres).
* Respect layering: **RPC → Service → Module → Provider → Data**.

---

## RPC Layer Rules

* Keep RPC thin: expressive, mapping, and security-only.
* Primary **role security** check occurs at the **domain level** (e.g., `urn:domain`).
* **Feature enablement** check occurs at the **subdomain level** (e.g., `urn:domain:subdomain`).
* Business logic must live in services/modules, never in RPC handlers.

---

## Module Initialization

* Two-phase startup:

  * **Instantiation**: load all `_module.py` files, attach to `app.state`.
  * **Startup**: run `startup()` coroutines, await dependencies with `on_ready()`, call `mark_ready()`.
* Always inherit from `BaseModule`.
* Always `await on_ready()` before using a module in startup.

---

## Solutions To Avoid

* Don’t add aliases when direct references exist.
* Don’t suppress errors.
* Don’t invent environment variables.
* Don’t put business logic in RPC.
* Don’t bypass modules by calling providers directly.

---

## File Structure

* `/` – Build automation, config, FastAPI entrypoint.
* `server/` – Modules, routes, helpers.
* `rpc/` – RPC handlers and services.
* `frontend/` – React app.
* `static/` – Generated frontend. 
* `tests/` – Unit/process tests. NOT A PYTHON MODULE! 
* `scripts/` – RPC-to-TS generation, schema, automation. NOT A PYTHON MODULE!
