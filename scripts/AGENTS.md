# Scripts AGENT Instructions

Guidelines for automation under `scripts/`, including RPC code generation and
operational tooling.

---

## General Rules

- Scripts are entry points, not importable packages. Keep them side-effect free
  on import—put work behind a `main()` guard.
- Reuse helpers from `scriptlib.py` for path resolution, version math, and
  Pydantic→TypeScript translation instead of re-implementing them.
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

- Use `mssql_cli.py` and helpers in `scriptlib.py` for schema work. Emit SQL to
  versioned files (e.g., `v0.x.y.z_timestamp.sql`) so humans can apply them via
  SSMS.
- `run_tests.py` is the canonical orchestration script for CI-style runs; keep it
  aligned with the commands listed in the root AGENT guide.
