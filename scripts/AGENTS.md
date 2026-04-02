# Scripts AGENT Instructions

Guidelines for automation under `scripts/`, including RPC code generation and
operational tooling.

---

## General Rules

- Scripts are entry points, not importable packages. Keep them side-effect free
  on import—put work behind a `main()` guard.
- Prefer extending existing scripts over adding new ad-hoc utilities.

---

## RPC Code Generation

- `generate_rpc_bindings.py` emits both `frontend/src/shared/RpcModels.tsx`
  and `frontend/src/rpc/*/index.ts` by harvesting Pydantic models and walking
  dispatcher maps. Run it whenever URNs, payload models, or service signatures
  change.
- Generated files include a banner from `HEADER_COMMENT`. Never edit the outputs
  manually—regenerate instead.
- Generated frontend artifacts (`frontend/src/rpc/`, `frontend/src/shared/RpcModels.tsx`,
  `frontend/src/db/namespace.ts`, `frontend/src/routes/registry.ts`) are excluded from
  source control and regenerated on every build. Never commit them. See PATTERNS.md §6.2.1.

---

## Database & Maintenance Utilities

- `run_cli.py` is the database management REPL entry point. It bootstraps
  `EnvModule` → `DbModule` → `DatabaseCliModule` and dispatches operations
  through the reflection `queryregistry` domain.
- Emit SQL schema changes as versioned files (for example,
  `v0.x.y.z_timestamp.sql`) so humans can apply them via SSMS.
- `v0.*.sql` files are historical schema archives and should be treated as
  immutable records.
- Active automation utilities in this folder include:
  - `generate_rpc_bindings.py`
  - `generate_db_namespace.py`
  - `generate_nav_pages.py`
  - `seed_rpcdispatch.py`
  - `seed_workflows.py`
  - `run_tests.py`
  - `cleanup_acr.py`
- `run_tests.py` is the canonical orchestration script for CI-style runs; keep
  it aligned with the commands listed in the root AGENT guide.

---

## Mechanical Automation Contracts

The code generation scripts use AST analysis to extract metadata from the
`rpc/` source tree. The following naming contracts are mechanically parsed:

- `DISPATCHERS` dict in each subdomain `__init__.py` — parsed by `parse_dispatchers`
  in `scripts/common.py`
- `HANDLERS` dict in each domain `__init__.py` — parsed by `parse_dict_keys`
  in `seed_rpcdispatch.py`
- `module` local variable in service functions — parsed by
  `parse_service_module_metadata` in `seed_rpcdispatch.py`
- `result: ModelName` type annotation in service functions — parsed by
  `parse_service_contracts` in `scripts/common.py`

These dict and variable names are fixed tokens that the AST crawlers match on.
See PATTERNS.md §0 for the full mechanical contracts reference and §6 for the
generation pipeline overview.
