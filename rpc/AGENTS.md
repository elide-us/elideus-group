# RPC AGENT Instructions

Rules for the RPC surface (`rpc/`), including request dispatchers, services,
and payload models.

---

## Handler Structure

- Domains register a top-level handler in `rpc/__init__.py`. Each domain module
  exposes a `HANDLERS` dict mapping the second URN segment to a handler
  function.
- Domain handlers select an operation-specific coroutine from their
  `DISPATCHERS` map. Dispatchers live in `__init__.py` next to `services.py` and
  are keyed by `(operation, version)` tuples.
- Service functions live in `services.py`. They must:
  - Call `unbox_request(request)` exactly once to obtain the parsed
    `RPCRequest` and `AuthContext`.
  - Pull modules from `request.app.state`, waiting on their `on_ready()` hooks
    if necessary before invoking business logic.

---

## Security & Validation

- Keep RPC handlers thin—authorization logic belongs in modules/services.
- Respect the domain-level role requirements documented in **ARCHITECTURE.md**
  and **RPC.md**. Only `auth.*` and `public.*` URNs may skip bearer token
  validation.
- Propagate FastAPI `HTTPException` instances; do not blanket catch exceptions
  without logging.

---

## Payload Contracts

- Define request/response models in `models.py` using Pydantic. These models are
  exported to TypeScript via the RPC generation scripts.
- When adding or changing URNs, update **RPC.md** and regenerate bindings by
  running `python scripts/generate_rpc_bindings.py`.
- Version bumps should add a new dispatcher entry instead of mutating the
  existing function in place.

---

## Mechanical Automation Contracts

The code generation pipeline (`scripts/seed_rpcdispatch.py`) uses AST analysis to extract metadata from service functions. The following naming contracts are required for the pipeline to function.

Service functions resolve their module using this pattern:

```python
module: RoleAdminModule = request.app.state.role_admin
await module.on_ready()
result = await module.list_roles(auth_ctx.role_mask)
```

The local variable is always `module`. The type annotation carries the specificity. The `request.app.state.{attr}` expression provides the ModuleManager registration name. The `module.{method}` call provides the method name. Both values are extracted by the AST crawler and stored in `reflection_rpc_functions`.

The `DISPATCHERS` dict in each subdomain `__init__.py` and the `HANDLERS` dict in each domain `__init__.py` are also parsed by name using AST analysis. These dicts must use exactly those names.

Refer to `scripts/seed_rpcdispatch.py` (`parse_service_module_metadata`, `parse_dict_keys`) and `scripts/common.py` (`parse_dispatchers`) for the crawler implementations.

## Anti-Patterns To Avoid

- Do **not** embed database access in RPC services—delegate to modules instead.
- Do **not** mutate global `HANDLERS`/`DISPATCHERS` state from tests without
  restoring it (see fixtures in `tests/`).
- Do **not** create ad-hoc URN shapes; follow `urn:{domain}:{subsystem}:{op}:{version}`.
