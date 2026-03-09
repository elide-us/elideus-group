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
  - `run_tests.py`
  - `cleanup_acr.py`
- `run_tests.py` is the canonical orchestration script for CI-style runs; keep
  it aligned with the commands listed in the root AGENT guide.
