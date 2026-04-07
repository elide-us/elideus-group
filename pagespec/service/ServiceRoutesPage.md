# Service Routes

**Route:** `/service-routes`

*Admin page for managing the application's navbar entries and route registry. Defines which pages appear in the navigation bar, their display names, icons, display sequence, and route group slug. Requires `ROLE_SERVICE_ADMIN`.*

## Purpose

The application has two related tables that drive frontend routing:

- **`frontend_pages`** — maps URL paths to React component filenames. Consumed by the build-time route registry generator (`generate_nav_pages.py`) which produces `frontend/src/routes/registry.ts`. This table is the source of truth for what pages exist.
- **`frontend_routes`** — defines navbar entries: which pages appear in the sidebar, their display name, icon, sequence, and route group. This is the table managed by this page.

This page manages `frontend_routes` only. The `frontend_pages` table is managed directly in the database (seed data / migrations).

## Page Layout

Row-edit table with inline create, edit, and delete. Columns:

| Column | Editable | Notes |
|---|---|---|
| Path | Yes (on create, immutable after) | URL path (e.g. `/service-routes`, `/gallery`) |
| Name | Yes | Display name in the navbar |
| Icon | Yes | MUI icon name (e.g. `Route`, `Storage`, `Settings`) |
| Slug | Yes | Route group slug (e.g. `service`, `system`, `finance`, `public`) — groups navbar entries under collapsible sections |
| Sequence | Yes | Display order within the slug group |
| Actions | — | Delete button |

New route row at the bottom with add button.

## Table: `frontend_routes`

| Column | Type | Notes |
|---|---|---|
| `recid` | BIGINT IDENTITY(1,1) | PK |
| `element_path` | NVARCHAR(256) | URL path, unique |
| `element_name` | NVARCHAR(256) | Display name |
| `element_icon` | NVARCHAR(256) | MUI icon name, nullable |
| `element_slug` | NVARCHAR(64) | Route group slug (e.g. `service`, `system`), nullable, default `NULL` |
| `element_sequence` | INT | Display order, default `0` |
| `element_roles` | BIGINT | Legacy role bitmask — retained for now, default `0`. Will be replaced by GUID-based role assignments when the security model is rebuilt. Not exposed in the UI. |
| `element_created_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |
| `element_modified_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |

*`element_roles` is no longer managed through this page. The column remains in the table with its current values but is not surfaced in the UI or in the RPC response. Access control for routes will be handled by the new GUID-based role/enablement system — see the Security Management page spec.*

## Table: `frontend_pages` (reference only — not managed by this page)

| Column | Type | Notes |
|---|---|---|
| `recid` | BIGINT IDENTITY(1,1) | PK |
| `element_path` | NVARCHAR(256) | URL path, unique |
| `element_component` | NVARCHAR(256) | React component path relative to `pages/` (e.g. `service/ServiceRoutesPage`) |
| `element_sequence` | INT | Build-time ordering, default `0` |

*Consumed by `generate_nav_pages.py` at build time. Not surfaced in this page — included here for context on the relationship between the two tables.*

## Functions

### `readRoutes`

- **Request:** none
- **Response:** `ReadRouteList1` — `{ elements: ReadRouteElement1[] }`
- `ReadRouteElement1` — `{ path: string, name: string, icon: string | null, slug: string | null, sequence: int }`

*Returns all rows from `frontend_routes` ordered by sequence. The `element_roles` column is not included in the response — access control is handled separately.*

### `upsertRoute`

- **Request:** `UpsertRouteParams1` — `{ path: string, name: string, icon: string | null, slug: string | null, sequence: int }`
- **Response:** `UpsertRouteResult1` — `{ path: string, name: string, icon: string | null, slug: string | null, sequence: int }`

*Updates if `element_path` exists, inserts if not. Sets `element_roles = 0` on insert (no role restriction). Sets `element_modified_on = SYSUTCDATETIME()` on update.*

### `deleteRoute`

- **Request:** `DeleteRouteParams1` — `{ path: string }`
- **Response:** `DeleteRouteResult1` — `{ path: string }`

## Route Group Slugs

The `element_slug` column replaces the former auto-segmenting behavior (which inferred groups from path prefixes). Slugs define how navbar entries are grouped under collapsible sections:

- `service` — Service admin pages (e.g. `/service-routes`, `/service-schema`, `/service-security`)
- `system` — System admin pages (e.g. `/system-config`, `/system-discord-management`)
- `finance` — Finance module pages (e.g. `/finance-accountant`, `/finance-manager`, `/finance-admin`)
- `public` — Public/registered user pages (e.g. `/gallery`, `/files`, `/wiki`)
- `NULL` — Top-level entries not grouped (e.g. `/`, `/login`)

The navbar component reads `element_slug` and groups entries accordingly. The slug is a free-text field — no lookup table — so new groups can be created by entering a new slug value.

## Notes

- The `element_roles` bitmask column is retained in the table but no longer managed through this page. The `required_roles` field that formerly appeared in the RPC response (resolved from the bitmask via `AuthModule.mask_to_names`) is removed. Route access control will be reimplemented under the new GUID-based security model.
- The `frontend_pages` and `frontend_routes` tables are separate concerns: `frontend_pages` maps paths to components (build-time), `frontend_routes` maps paths to navbar display properties (runtime). A route can exist in `frontend_pages` without a `frontend_routes` entry (page exists but has no navbar link) and vice versa (though a navbar link without a page entry would be a dead link).
- The `element_slug` column is new — it needs to be added to `frontend_routes` via migration. Existing rows should be seeded with slugs derived from their current path prefixes during migration.

## Description

Service route management page. Row-edit table for managing navbar entries in `frontend_routes`: path, display name, icon, route group slug, and display sequence. Supports inline create, edit, and delete. Route group slugs replace the former auto-segmenting behavior — entries are grouped in the navbar by slug value. Role-based access control for routes is deferred to the new security model; the legacy bitmask column is retained but not surfaced.