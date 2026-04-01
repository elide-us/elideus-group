# RPC AGENT Instructions

Rules for the RPC surface (`rpc/`), including request dispatchers, services,
and payload models. Refer to **PATTERNS.md** for canonical code examples.

---

## Canonical Reference

The `reflection_rpc_*` database tables are the authoritative catalog of every
RPC domain, subdomain, function, model, and model field. The code in `rpc/`
is the source that generates this catalog. Query the MCP service
(`oracle_list_rpc_functions`, `oracle_list_rpc_models`, etc.) to inspect the
live registered state.

---

## Handler Structure

- Domains register a top-level handler in `rpc/__init__.py` via a `HANDLERS` dict
  mapping domain names to handler functions.
- Domain handlers route to subdomains via their own `HANDLERS` dict.
- Subdomains route to service functions via a `DISPATCHERS` dict keyed by
  `(operation, version)` tuples.
- Service functions are security routers: authenticate, authorize, dispatch to
  module, pass through the response. See PATTERNS.md §2.6 for the canonical pattern.

---

## Mechanical Automation Contracts

The code generation pipeline (`scripts/seed_rpcdispatch.py`) uses AST analysis
to extract metadata from service functions. The following naming contracts are
mechanically parsed — the pipeline matches on exact token names in the syntax tree.

Service functions resolve their module using this exact pattern:

```python
module: RoleAdminModule = request.app.state.role_admin
await module.on_ready()
result: AccountRoleList1 = await module.list_roles(auth_ctx.role_mask)
```

The local variable is always `module`. The type annotation carries the specificity.
The `request.app.state.{attr}` expression provides the ModuleManager registration
name. The `module.{method}` call provides the method name. Both values are extracted
by the AST crawler and stored in `reflection_rpc_functions`.

The `result` variable must have a type annotation matching the response Pydantic model.
The binding generator uses this to determine the TypeScript return type.

The `DISPATCHERS` dict in each subdomain `__init__.py` and the `HANDLERS` dict in
each domain `__init__.py` are also parsed by name using AST analysis. These dicts
must use exactly those names.

Refer to `scripts/seed_rpcdispatch.py` (`parse_service_module_metadata`,
`parse_dict_keys`) and `scripts/common.py` (`parse_dispatchers`, `parse_service_contracts`)
for the crawler implementations.

---

## Security & Validation

- RPC service functions are thin security routers with zero business logic and
  zero data transformation. All business logic lives in modules.
- Only `auth.*` and `public.*` URNs may skip bearer token validation.
- Propagate `HTTPException` instances with contextual detail.

---

## Payload Contracts

- Define request/response models in `models.py` using Pydantic. These models are
  exported to TypeScript via the RPC generation scripts.
- Modules return the RPC response Pydantic model directly. The service function
  passes it through via `result.model_dump()`.
- When adding or changing URNs, regenerate bindings by running
  `python scripts/generate_rpc_bindings.py`.
- Version bumps add a new dispatcher entry rather than mutating the existing function.
