# System Conversations

**Route:** `/system-conversations`

## Table: `system_conversations` (rename from `assistant_conversations`)

| Column | Type | Notes |
|---|---|---|
| `recid` | BIGINT IDENTITY(1,1) | PK |
| `element_thread_id` | BIGINT | Groups messages into threads |
| `conversation_roles_recid` | BIGINT | FK → `system_conversation_roles.recid`, indexed, lead predicate filter |
| `element_content` | NVARCHAR(MAX) | Message content, nullable |
| `element_tokens` | INT | Token usage for this message, nullable |
| `element_is_flagged` | BIT | Moderation flag — hides from content display, default `0` |
| `personas_guid` | UNIQUEIDENTIFIER | FK → `system_personas.element_guid` |
| `models_guid` | UNIQUEIDENTIFIER | FK → `service_models.element_guid` |
| `users_guid` | UNIQUEIDENTIFIER | FK → `account_users.element_guid`, nullable |
| `guilds_guid` | UNIQUEIDENTIFIER | FK → `discord_guilds.element_guid`, nullable |
| `element_created_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |
| `element_modified_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |

## Lookup Table: `system_conversation_roles`

| Column | Type | Notes |
|---|---|---|
| `recid` | BIGINT | IDENTITY(1,1) | PK |
| `element_name` | NVARCHAR(16) | Role name (`user`, `assistant`, `system`) |

*Enumeration table — seed values: `user`, `assistant`, `system`.*

## Indexing

- `conversation_roles_recid` should be the **lead column** in predicate order for filtered queries. High selectivity on role narrows result sets early.
- Existing indexes on `element_thread_id` and `element_created_on` are retained.

## Functions

### `readConversationSummary`

- **Request:** none
- **Response:** `ReadConversationSummaryResult1` — `{ total_threads: int, total_messages: int, total_tokens: int, oldest_entry: string | null, newest_entry: string | null }`

### `readConversationHeaders`

- **Request:** `ReadConversationHeadersParams1` — `{ limit: int, offset: int }`
- **Response:** `ReadConversationHeaderList1` — `{ elements: ReadConversationHeaderElement1[] }`
- `ReadConversationHeaderElement1` — `{ thread_id: int, persona_name: string, model_name: string, user_display_name: string | null, guild_name: string | null, message_count: int, total_tokens: int, is_flagged: bool, first_message_on: string, last_message_on: string }`

### `readConversationLines`

- **Request:** `ReadConversationLinesParams1` — `{ thread_id: int }`
- **Response:** `ReadConversationLineList1` — `{ elements: ReadConversationLineElement1[] }`
- `ReadConversationLineElement1` — `{ recid: int, role_name: string, content: string | null, tokens: int | null, is_flagged: bool, persona_name: string, model_name: string, user_display_name: string | null, guild_name: string | null, created_on: string }`

### `flagConversation`

- **Request:** `FlagConversationParams1` — `{ recid: int, is_flagged: bool }`
- **Response:** `FlagConversationResult1` — `{ recid: int, is_flagged: bool }`

### `deleteConversationThread`

- **Request:** `DeleteConversationThreadParams1` — `{ thread_id: int }`
- **Response:** `DeleteConversationThreadResult1` — `{ thread_id: int, deleted_count: int }`

## Canonical Form Pattern: Summary + Headers + Lines

This page establishes the canonical pattern for summary/header/line views used elsewhere in the application (journals, ledgers, etc.):

1. **Summary view** — aggregate stats across all data
2. **Header list** — paginated list of grouped records (threads), click to select
3. **Line detail** — messages within the selected thread, with element-level metadata

Future state: summary and headers on one page, lines + element detail on a drill-down page. Element detail view (not yet implemented) should show: persona used, API model used, sending user, guild context, credit usage.

## GDPR Compliance

- Moderators **cannot edit** message content directly.
- Moderators **can flag** a conversation/message so it is hidden from content display, but the content itself is **not deleted** — it is retained for legal/audit purposes.
- Flagged users follow downstream moderation flows (TBD) — similar to the user panel pattern where moderators can only set a display name to the literal `"Default User"`, not to arbitrary values.
- Bulk deletion by date is not supported — records retention policies are handled by a separate compliance process.

## Notes

- Data is cross-domain — joins to `system_personas`, `service_models`, `account_users`, `discord_guilds` for display names.
- `role_name` in response models is a denormalized display field resolved from the `system_conversation_roles` FK join.
- Legacy string Discord IDs (`element_guild_id`, `element_channel_id`, `element_user_id`) and `element_input`/`element_output` columns are removed in the redesign, replaced by GUID FKs and `element_content` + role FK.
- `service_models` (renamed from `assistant_models`) and `system_personas` (renamed from `assistant_personas`) FK references migrate from `recid` to GUID-based FKs.

## Description

Page displays conversation thread data in the canonical summary + headers + lines pattern. Summary shows aggregate stats. Headers list threads with metadata (persona, model, user, guild, message count, tokens, flagged status). Selecting a header shows individual messages. Primary purpose is moderation with GDPR-compliant controls: flag to hide (not delete), content retained for audit.