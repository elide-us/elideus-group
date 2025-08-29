# Frontend AGENT Instructions

- Keep shared, reusable pieces in `src/components` and route-level views in `src/pages`.
- The Vite config (`vite.config.ts`) groups chunks by top-level route prefixes such as `system-*` and `admin-*`. When adding new route groups or modifying existing ones, update `manualChunks` accordingly.
