# Server AGENT Instructions

These rules cover the FastAPI application (`server/`), including modules,
providers, routers, and helper utilities.

---

## Layering Expectations

- Respect the project layering from **ARCHITECTURE.md**: RPC → Service → Module
  → Provider. Server code owns the Module and Provider layers.
- FastAPI routers (`server/routers`) should forward requests to modules or RPC
  handlers without embedding business logic.

---

## Module Lifecycle

- Modules live in `server/modules` and must define a `CamelCaseModule` class in a
  `*_module.py` file. The `ModuleManager` instantiates them automatically during
  app startup (`server/lifespan.py`).
- Always inherit from `BaseModule`. Call `mark_ready()` once initialization
  completes so other modules can await `on_ready()` safely.
- Acquire dependencies from `app.state.<module_name>` and `await on_ready()`
  before using them inside `startup()`.
- Avoid global singletons; store runtime state on the module instance.

---

## Providers and Registry Usage

- Provider implementations live under `server/modules/providers`. Keep them
  focused on connection management and external API interactions.
- Database SQL stays in the registry layer (`server/registry`). Modules should
  call `DbModule.run()` with registry request objects rather than embedding raw
  queries.
- When adding a provider, expose configuration through `EnvModule` and wire it
  into the owning module's startup routine.

---

## Operational Guidance

- Changes that touch authentication or role resolution must preserve the
  security contracts described in **AUTHENTICATION_DIAGRAMS.md**.
- If module startup requires migrations or seed data, produce `.sql` files under
  `scripts/` and document manual steps.
- Keep logging structured (`[Module] message`). Avoid suppressing exceptions—log
  and re-raise so RPC callers receive accurate errors.

---

## Anti-Patterns To Avoid

- Do **not** bypass modules by importing providers directly from RPC code.
- Do **not** perform blocking I/O in startup without `await`; use async helpers
  from existing providers.
- Do **not** mutate `app.state` outside of the module manager unless you are
  intentionally registering a module-level API.
