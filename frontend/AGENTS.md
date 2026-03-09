# Frontend AGENT Instructions

Guidance for the Vite + React + TypeScript app under `frontend/`.

---

## What this layer IS

- A presentation/UI layer for rendering state and collecting user intent.
- React components, route pages, and composition of generated RPC clients.

## What this layer is NOT

- Not a home for backend business rules.
- Not a place to hand-maintain API schema bindings.
- Not a place to mirror query registry dispatch logic.

---

## Key files and directories

- `frontend/src/components` – reusable UI building blocks.
- `frontend/src/pages` – route-level screens.
- `frontend/src/shared` – shared contexts, theme, and runtime frontend configuration.
- `frontend/src/rpc` – generated TypeScript RPC bindings (**do not edit manually**).
- `frontend/vite.config.ts` – chunking/build strategy (route-group chunk mapping).

Adjacent guidance:
- Root `AGENTS.md` for repository-wide workflow/test expectations.
- `rpc/AGENTS.md` for backend RPC definitions that drive generated frontend bindings.
- `queryregistry/AGENTS.md` for canonical server-side query dispatch conventions.

---

## Component patterns and naming

- Prefer functional components with hooks.
- Keep components focused/presentational; pass business decisions in via props/hooks.
- Component naming:
  - files/components: `PascalCase.tsx` for exported components.
  - hooks/utilities local to UI: `camelCase.ts`.
- Co-locate view-specific styles/assets with their components when practical.

---

## RPC and typing workflow

- Use generated clients in `src/rpc`; do not hand-edit generated files.
- When RPC contracts change, regenerate bindings from Python RPC definitions using
  `python scripts/generate_rpc_bindings.py`.
- Keep TypeScript types aligned with backend models via regeneration, not manual patching.

---

## Anti-patterns (forbidden)

- Embedding backend/domain business logic in components.
- Creating frontend-side compatibility shims for deprecated backend operation names.
- Bypassing generated RPC clients with ad-hoc request shapes when bindings exist.
- Introducing aliases where direct references already exist.
