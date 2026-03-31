# RPC Patterns

Canonical patterns for RPC domain handlers, subdomain dispatchers, and service implementations.

## 0. Mechanical Automation Contracts

The code generation pipeline uses AST analysis to crawl RPC service functions and extract metadata. The following naming contracts are mechanically parsed — the pipeline matches on exact token names in the syntax tree.

### 0.1 Service Function Module Variable

Every RPC service function resolves its module using this exact pattern:

```python
module: SystemConfigModule = request.app.state.system_config
await module.on_ready()
result = await module.get_configs(auth_ctx.user_guid, auth_ctx.roles)
```

The local variable is always named `module`. The type annotation (e.g., `SystemConfigModule`) carries the specificity. The right side of the assignment (e.g., `request.app.state.system_config`) is the ModuleManager registration name.

The seed script `scripts/seed_rpcdispatch.py` function `parse_service_module_metadata` extracts:
- `element_module_attr` from the `request.app.state.{attr}` expression
- `element_method_name` from the `module.{method}` call expression

These values populate the `reflection_rpc_functions` table and drive code generation. Refer to `scripts/seed_rpcdispatch.py` for the AST crawler implementation.

### 0.2 DISPATCHERS Dict

Every RPC subdomain `__init__.py` exports a `DISPATCHERS` dict keyed by `(operation, version)` tuples:

```python
DISPATCHERS: dict[tuple[str, str], callable] = {
  ("get_configs", "1"): system_config_get_configs_v1,
}
```

The seed script `scripts/seed_rpcdispatch.py` function `parse_dict_keys` and the binding generator `scripts/common.py` function `parse_dispatchers` both parse this dict by name using AST analysis. The dict must be named `DISPATCHERS`.

### 0.3 HANDLERS Dict

Every RPC domain `__init__.py` exports a `HANDLERS` dict mapping subdomain names to handler functions:

```python
HANDLERS: dict[str, callable] = {
  "config": handle_config_request,
}
```

The seed script uses `parse_dict_keys` to discover subdomains from this dict. The dict must be named `HANDLERS`.
