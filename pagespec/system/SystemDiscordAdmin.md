# Discord Management

**Route:** `/system-discord-management`

*Combines the former DiscordGuildsPage (`/discord-guilds`) and DiscordPersonasPage (`/discord-personas`) into a unified Discord administration page.*

## Table: `discord_guilds`

| Column | Type | Notes |
|---|---|---|
| `element_guid` | UNIQUEIDENTIFIER | PK, deterministic from `element_guild_id`, unique |
| `element_guild_id` | NVARCHAR(64) | Discord snowflake ID, unique |
| `element_name` | NVARCHAR(256) | Guild display name, synced from Discord API |
| `element_owner_id` | NVARCHAR(64) | Discord snowflake of guild owner, nullable |
| `element_region` | NVARCHAR(128) | Guild region, nullable |
| `element_member_count` | INT | Synced member count, nullable |
| `element_credits` | INT | Guild credit allocation, default `0` |
| `element_notes` | NVARCHAR(MAX) | Admin notes, nullable |
| `element_joined_on` | DATETIMEOFFSET(7) | When bot joined guild, default `SYSUTCDATETIME()` |
| `element_left_on` | DATETIMEOFFSET(7) | When bot left guild, nullable |
| `element_created_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |
| `element_modified_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |

## Table: `discord_channels`

| Column | Type | Notes |
|---|---|---|
| `element_guid` | UNIQUEIDENTIFIER | PK, deterministic from `element_channel_id`, unique |
| `guilds_guid` | UNIQUEIDENTIFIER | FK → `discord_guilds.element_guid` |
| `element_channel_id` | NVARCHAR(64) | Discord snowflake ID |
| `element_name` | NVARCHAR(256) | Channel name, nullable |
| `element_type` | NVARCHAR(32) | Channel type, nullable |
| `element_message_count` | BIGINT | Tracked message count, default `0` |
| `element_last_activity_on` | DATETIMEOFFSET(7) | Last message timestamp, nullable |
| `element_notes` | NVARCHAR(MAX) | Admin notes, nullable |
| `element_created_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |
| `element_modified_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |

## Table: `system_personas` (rename from `assistant_personas`)

| Column | Type | Notes |
|---|---|---|
| `element_guid` | UNIQUEIDENTIFIER | PK, deterministic from `element_name`, unique |
| `element_name` | NVARCHAR(256) | Persona name, unique |
| `element_prompt` | NVARCHAR(MAX) | System prompt template |
| `element_tokens` | INT | Max token limit for responses |
| `element_is_active` | BIT | Active toggle, default `1` |
| `models_guid` | UNIQUEIDENTIFIER | FK → `service_models.element_guid` |
| `element_notes` | NVARCHAR(MAX) | Admin notes, nullable |
| `element_created_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |
| `element_modified_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |

*Removes legacy `element_metadata` JSON column — structured fields replace it. `models_recid` FK migrates to GUID-based `models_guid`.*

## Functions — Guilds

### `readGuilds`

- **Request:** none
- **Response:** `ReadGuildList1` — `{ elements: ReadGuildElement1[] }`
- `ReadGuildElement1` — `{ guid: string, guild_id: string, name: string, owner_id: string | null, region: string | null, member_count: int | null, credits: int, notes: string | null, joined_on: string, left_on: string | null }`

### `syncGuilds`

- **Request:** none
- **Response:** `SyncGuildsResult1` — `{ elements: ReadGuildElement1[], synced_count: int }`

### `updateGuild`

- **Request:** `UpdateGuildParams1` — `{ guid: string, credits: int, notes: string | null }`
- **Response:** `UpdateGuildResult1` — `{ guid: string, credits: int, notes: string | null }`

## Functions — Personas

### `createPersona`

- **Request:** `CreatePersonaParams1` — `{ name: string, prompt: string, tokens: int, models_guid: string, is_active: bool, notes: string | null }`
- **Response:** `CreatePersonaResult1` — `{ guid: string, name: string, prompt: string, tokens: int, models_guid: string, model_name: string, is_active: bool, notes: string | null }`

### `readPersonas`

- **Request:** none
- **Response:** `ReadPersonaList1` — `{ elements: ReadPersonaElement1[] }`
- `ReadPersonaElement1` — `{ guid: string, name: string, prompt: string, tokens: int, models_guid: string, model_name: string, is_active: bool, notes: string | null }`

### `updatePersona`

- **Request:** `UpdatePersonaParams1` — `{ guid: string, prompt: string, tokens: int, models_guid: string, is_active: bool, notes: string | null }`
- **Response:** `UpdatePersonaResult1` — `{ guid: string, name: string, prompt: string, tokens: int, models_guid: string, model_name: string, is_active: bool, notes: string | null }`

### `deletePersona`

- **Request:** `DeletePersonaParams1` — `{ guid: string }`
- **Response:** `DeletePersonaResult1` — `{ guid: string }`

## Functions — Shared Lookups

### `readModels`

- **Request:** none
- **Response:** `ReadModelList1` — `{ elements: ReadModelElement1[] }`
- `ReadModelElement1` — `{ guid: string, name: string }`

*Read-only lookup for the persona model dropdown. Returns active models from `service_models`.*

## Notes

- Guild fields synced from Discord API (`name`, `owner_id`, `region`, `member_count`) are read-only. Only `credits` and `notes` are user-editable.
- `syncGuilds` pulls current guild state from the Discord API and upserts.
- `discord_channels` is included in the table redesign but not directly surfaced in this page — channels are managed via sync and used by the bot backend.
- `model_name` in persona response models is a denormalized display field resolved from `service_models` FK join.
- Persona `element_name` is immutable after creation (deterministic GUID source).
- `system_conversations` references both `system_personas` and `discord_guilds` via GUID FKs — those references must align with these table redesigns.

## Description

Unified Discord administration page. Guilds section displays registered Discord servers in an editable table — synced fields (name, member count, region) are read-only, admin fields (credits, notes) are editable, with a sync button to pull latest data from Discord API. Personas section displays bot persona definitions in an editable table with model dropdown from `service_models`, prompt editing, token limits, and active toggle. Uses the shared row-edit control and application theme throughout.