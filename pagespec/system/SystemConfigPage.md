# System Configuration

**Route:** `/system-config`

## Table: `system_config`

| Column | Type | Notes |
|---|---|---|
| `element_guid` | UNIQUEIDENTIFIER | PK, deterministic from `element_key`, unique |
| `element_key` | NVARCHAR(1024) | Unique config key |
| `element_value` | NVARCHAR(MAX) | Config value |
| `element_created_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |
| `element_modified_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |

## Functions

### `createConfig`

- **Request:** `CreateConfigParams1` — `{ key: string, value: string }`
- **Response:** `CreateConfigResult1` — `{ guid: string, key: string, value: string }`

### `readConfig`

- **Request:** none
- **Response:** `ReadConfigList1` — `{ elements: ReadConfigElement1[] }`
- `ReadConfigElement1` — `{ guid: string, key: string, value: string }`

### `updateConfig`

- **Request:** `UpdateConfigParams1` — `{ guid: string, key: string, value: string }`
- **Response:** `UpdateConfigResult1` — `{ guid: string, key: string, value: string }`

### `deleteConfig`

- **Request:** `DeleteConfigParams1` — `{ guid: string }`
- **Response:** `DeleteConfigResult1` — `{ guid: string }`

## Description

Page displays key-value pairs from `system_config` in an editable table using the shared row-edit control and application theme. Supports inline create, edit (upsert), and delete.