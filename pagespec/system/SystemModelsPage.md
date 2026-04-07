# System Models

**Route:** `/system-models`

## Table: `system_models` (rename from `assistant_models`)

| Column | Type | Notes |
|---|---|---|
| `element_guid` | UNIQUEIDENTIFIER | PK, deterministic from `element_name`, unique |
| `element_name` | NVARCHAR(128) | Model identifier (e.g. `gpt-4o-mini`), unique, imported |
| `api_providers_guid` | UNIQUEIDENTIFIER | FK → `service_api_providers.element_guid` |
| `element_is_active` | BOOL | User-controlled active toggle |
| `element_notes` | NVARCHAR(MAX) | User-editable annotation, nullable |
| `element_created_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |
| `element_modified_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |

## Lookup Table: `service_api_providers`

| Column | Type | Notes |
|---|---|---|
| `element_guid` | UNIQUEIDENTIFIER | PK, deterministic from `element_name`, unique |
| `element_name` | NVARCHAR(64) | Provider name (e.g. `openai`, `lumalabs`) |
| `element_created_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |
| `element_modified_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |

*`service_api_providers` is managed separately (future provider configuration page). This page consumes it as a read-only dropdown.*

## Functions

### `createModel`

- **Request:** `CreateModelParams1` — `{ name: string, api_providers_guid: string, is_active: bool, notes: string | null }`
- **Response:** `CreateModelResult1` — `{ guid: string, name: string, api_providers_guid: string, api_provider_name: string, is_active: bool, notes: string | null }`

### `readModels`

- **Request:** none
- **Response:** `ReadModelList1` — `{ elements: ReadModelElement1[] }`
- `ReadModelElement1` — `{ guid: string, name: string, api_providers_guid: string, api_provider_name: string, is_active: bool, notes: string | null }`

### `updateModel`

- **Request:** `UpdateModelParams1` — `{ guid: string, is_active: bool, notes: string | null }`
- **Response:** `UpdateModelResult1` — `{ guid: string, name: string, api_providers_guid: string, api_provider_name: string, is_active: bool, notes: string | null }`

### `deleteModel`

- **Request:** `DeleteModelParams1` — `{ guid: string }`
- **Response:** `DeleteModelResult1` — `{ guid: string }`

## Notes

- `name` and `api_providers_guid` are read-only for imported models. Only `is_active` and `notes` are user-editable on import-sourced rows.
- `api_provider_name` is a denormalized display field resolved from the FK join — not stored on `assistant_models`.
- This page may relocate to a different domain in the rebuild (currently `system:models`, table is `assistant_models`).
- Future: automated import workflow pulls available models from provider APIs.
- `assistant_personas.models_recid` FK references this table — will need migration to GUID-based FK when personas table is redesigned.

## Description

Page displays AI model registrations in an editable table using the shared row-edit control and application theme. Imported model fields (name, provider) are read-only; user fields (active, notes) are editable. Provider selection is a dropdown populated from `service_api_providers`. Supports manual create and delete.