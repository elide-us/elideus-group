# Frontend AGENT Instructions

Guidance for the Vite/React application under `frontend/`.

---

## Project Layout

- Place shared, reusable UI pieces in `src/components`. Route-level screens live
  in `src/pages`.
- Configuration for runtime services (feature flags, themes) belongs in
  `src/shared`. Keep RPC adapters in `src/rpc`; those files are generated—do not
  edit them by hand.

---

## Build & Tooling

- The Vite config (`vite.config.ts`) groups chunks by top-level route prefixes
  such as `system-*` and `admin-*`. When adding new route groups or changing
  directory structure, update the `manualChunks` logic to keep bundles stable.
- Run `npm lint`, `npm type-check`, and `npm test` before submitting changes.
  Vitest specs live in `frontend/tests`.

---

## UI & State Conventions

- Prefer functional components with hooks. Shared context providers reside in
  `src/shared`; extend them instead of adding ad-hoc global state.
- Co-locate component-specific styles with the component. Follow the theme tokens
  defined in `src/shared/ElideusTheme.tsx` when adding new colors or spacing.

---

## RPC Integration

- Consume backend APIs through the generated helpers in `src/rpc`. If a helper is
  missing, add the corresponding dispatcher in the RPC layer and rerun
  `python scripts/generate_rpc_bindings.py`.
- Keep request/response typing in sync with Pydantic models—regenerate bindings
  rather than editing TypeScript signatures manually.
