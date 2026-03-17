# Repository-wide AGENT Instructions

This document sets the ground rules for any change that spans the repository.
Component-specific expectations now live beside the code they regulate; see the
"Component Guides" section below before editing a feature area.

---

## Orientation

- Review **ARCHITECTURE.md** for the layer boundaries (RPC → Service → Module →
  Provider) and the security model.
- Domain-specific design notes are captured in the markdown files that live next
  to the related code (for example **RPC.md** and documents under `server/`).

---

## Workflow Guardrails

- Update tests, scripts, and documentation alongside code changes.
- Database loads must be delivered as `.sql` files—humans run them through
  **SSMS**.
- Migration SQL scripts go in `migrations/`, never at the repo root.
  The repo root holds only the tagged release baseline files
  (`v{version}_YYYYMMDD.sql` and `v{version}_seed_YYYYMMDD.sql`).
  See `migrations/AGENTS.md` for versioning and naming rules.
- Prefer existing automation helpers when they exist instead of ad-hoc scripts.
- Docker builds have no automated coverage—plan manual validation when touching
  the Dockerfile or startup scripts.

---

## Common Pitfalls to Avoid

- Do not add aliases when a direct reference is already available.
- Do not suppress errors; surface them with contextual logging.
- Do not invent new environment variables without updating configuration docs
  and module startup code.

---

## Build & Test Entry Points

- **Unified harness** – run `python scripts/run_tests.py` to execute the
  standard lint, type-check, and test pipeline shared by local, CI, and YAML
  automation environments.
- **Python / FastAPI** – run `pytest` from the `tests/` directory when iterating
  on backend code; the unified harness calls into this command.
- **Frontend** – run `npm lint`, `npm type-check`, and `npm test` for focused
  feedback; these steps are orchestrated automatically by the unified harness.
- **Tooling** – prefer `python scripts/run_tests.py` over ad-hoc shell
  sequences. Use `dev.cmd` for Windows workflows that need parity with the
  harness.

---

## Coding Conventions

- Python uses **2-space** indentation.
- TypeScript uses **4-space tabs**.
- Keep formatting and lint passes clean before opening a PR.

---

## Component Guides

Consult these scoped instruction files when working in a given area:

- `frontend/AGENTS.md` – React/Vite codebase.
- `rpc/AGENTS.md` – RPC handlers and services.
- `server/AGENTS.md` – FastAPI app startup, modules, and providers.
- `server/mcp_server.py` – MCP server for LLM schema discovery (read-only).
- `scripts/AGENTS.md` – Automation and RPC binding generation.
- `tests/AGENTS.md` – Python test suite structure.

Always obey the most specific AGENTS.md covering the files you modify.
