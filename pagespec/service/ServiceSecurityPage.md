# Security Management

**Route:** `/service-security`

*Replaces the former ServiceRolesPage (`/service-roles`). Defines the security primitives for the platform — roles (domain access) and enablements (subdomain/feature access). The bitmask system is being replaced with GUID-keyed deterministic entries.*

## Security Model

Two types of security entries, stored in the same table, differentiated by prefix convention:

### Roles (`ROLE_` prefix)
Domain-level access gates. Each role maps to an RPC domain. The role name follows the pattern `ROLE_{DESCRIPTOR}` where the descriptor identifies the access tier.

Roles are subdivided into audit tiers:

- **USER roles** — standard access roles. Not specifically audit logged beyond moderation flows.
- **ADMIN roles** — elevated access roles. All actions are audit logged.
- **Duty-split roles** — specific Segregation of Duties splits within a domain (e.g. `ROLE_FINANCE_ACCT` vs `ROLE_FINANCE_APPR`).

### Enablements (`ENABLE_` prefix)
Subdomain and feature-level access gates. These are finer-grained permissions that control access to specific capabilities within a domain. Enablements are always gated behind a prerequisite role.

Examples:
- `ENABLE_OPENAI` → access to OpenAI API generation (requires `ROLE_STORAGE`)
- `ENABLE_LUMAAI` → access to LumaAI video generation (requires `ROLE_STORAGE`)
- `ENABLE_DISCORD_CHAT` → access to Discord chat persona features (requires `ROLE_DISCORD_USER`)
- `ENABLE_DISCORD_TTS` → access to Discord TTS features (requires `ROLE_DISCORD_USER`)
- `ENABLE_MCP` → access to MCP agent tools

## Table: `system_roles` (redesign)

| Column | Type | Notes |
|---|---|---|
| `element_guid` | UNIQUEIDENTIFIER | PK, deterministic from `element_name` (uuid5), unique |
| `element_name` | NVARCHAR(128) | Role/enablement key (e.g. `ROLE_SYSTEM_ADMIN`, `ENABLE_OPENAI`), unique |
| `element_display` | NVARCHAR(256) | Human-readable display name |
| `element_description` | NVARCHAR(512) | Description of what this entry grants, nullable |
| `element_type` | NVARCHAR(16) | `role` or `enablement` — derived from prefix but stored for indexing |
| `element_audit_tier` | NVARCHAR(16) | `user`, `admin`, or `duty` — controls audit logging behavior, nullable for enablements |
| `element_rpc_domain` | NVARCHAR(64) | Associated RPC domain (for roles), nullable |
| `element_rpc_subdomain` | NVARCHAR(64) | Associated RPC subdomain (for enablements), nullable |
| `element_is_active` | BIT | Active flag, default `1` |
| `element_created_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |
| `element_modified_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |

*Drops `recid`, `element_mask`, and `element_enablement` columns from the old schema. The bitmask system is fully replaced by GUID-based role assignment in `users_roles` (schema TBD — see Notes).*

## Functions

### `readSecurityEntries`

- **Request:** none
- **Response:** `ReadSecurityEntryList1` — `{ elements: ReadSecurityEntryElement1[] }`
- `ReadSecurityEntryElement1` — `{ guid: string, name: string, display: string, description: string | null, type: string, audit_tier: string | null, rpc_domain: string | null, rpc_subdomain: string | null, is_active: bool }`

### `createSecurityEntry`

- **Request:** `CreateSecurityEntryParams1` — `{ name: string, display: string, description: string | null, audit_tier: string | null, rpc_domain: string | null, rpc_subdomain: string | null }`
- **Response:** `CreateSecurityEntryResult1` — `{ guid: string, name: string, type: string }`

*GUID is generated server-side as `uuid5(namespace, name)`. Type is derived from the name prefix (`ROLE_` → `role`, `ENABLE_` → `enablement`).*

### `updateSecurityEntry`

- **Request:** `UpdateSecurityEntryParams1` — `{ guid: string, display: string | null, description: string | null, audit_tier: string | null, rpc_domain: string | null, rpc_subdomain: string | null, is_active: bool | null }`
- **Response:** `UpdateSecurityEntryResult1` — `{ guid: string }`

*`element_name` is immutable after creation (it's the deterministic GUID source).*

### `deleteSecurityEntry`

- **Request:** `DeleteSecurityEntryParams1` — `{ guid: string }`
- **Response:** `DeleteSecurityEntryResult1` — `{ guid: string }`

## Seed Data — Roles

| Name | Display | Audit Tier | RPC Domain |
|---|---|---|---|
| `ROLE_REGISTERED_USER` | Registered User | user | users |
| `ROLE_STORAGE` | Storage Access | user | storage |
| `ROLE_SUPPORT_USER` | Support | user | support |
| `ROLE_MODERATOR_USER` | Moderator | user | moderation |
| `ROLE_DISCORD_USER` | Discord User | user | discord |
| `ROLE_ACCOUNT_ADMIN` | Account Admin | admin | account |
| `ROLE_SYSTEM_ADMIN` | System Admin | admin | system |
| `ROLE_SERVICE_ADMIN` | Service Admin | admin | service |
| `ROLE_DISCORD_ADMIN` | Discord Admin | admin | discord |
| `ROLE_FINANCE_ACCT` | Accountant | duty | finance |
| `ROLE_FINANCE_APPR` | Accounting Manager | duty | finance |
| `ROLE_FINANCE_ADMIN` | Finance Admin | admin | finance |

### Audit Tier Rules
- **`user`** — actions are not specifically audit logged beyond standard moderation flows
- **`admin`** — all actions performed under this role are audit logged
- **`duty`** — Segregation of Duties split; `ROLE_FINANCE_ACCT` (create/submit) and `ROLE_FINANCE_APPR` (approve/reject) cannot overlap for the same user in controlled workflows

### Role Notes
- `ROLE_STORAGE` is a **role**, not an enablement, because it is a prerequisite gate for multiple enablements (content tools, generation services, etc.) and grants access to the file manager and related storage features
- `ROLE_DISCORD_USER` enables interacting with the Discord bot in various ways — like storage, it will have rich enablements defined under it (TBD)

## Seed Data — Enablements

| Name | Display | Prerequisite | Notes |
|---|---|---|---|
| `ENABLE_OPENAI` | OpenAI Generation | `ROLE_STORAGE` | Was `ROLE_OPENAI_API` |
| `ENABLE_LUMAAI` | LumaAI Generation | `ROLE_STORAGE` | Was `ROLE_LUMAAI_API` |
| `ENABLE_MCP` | MCP Agent Access | — | Was `ROLE_MCP_ACCESS` |
| `ENABLE_DISCORD_BOT` | Discord Bot | `ROLE_DISCORD_USER` | Was `ROLE_DISCORD_BOT` |
| `ENABLE_DISCORD_CHAT` | Discord Chat | `ROLE_DISCORD_USER` | New |
| `ENABLE_DISCORD_TTS` | Discord TTS | `ROLE_DISCORD_USER` | New |

## Page UI

Row-edit table with all security entries. Columns: Name | Display | Type | Audit Tier | Domain | Subdomain | Active | Actions. Type column shows `role` or `enablement` chip. Audit tier column shows `user`, `admin`, or `duty` chip (blank for enablements). Supports create (add row), update (inline edit display/description/tier/domain/subdomain/active), and delete. Name is immutable after creation.

## Notes

- The `users_roles` table currently stores a bitmask. This will be replaced by a junction table pattern (user GUID + role GUID) — that redesign is separate from this page spec but is a prerequisite for the new security model to function.
- All GUIDs are deterministic: `uuid5(RPC_REFLECTION_NAMESPACE, element_name)` — same namespace used by the RPC reflection seed system.
- The `element_type` column is derived from the name prefix on create and stored for query convenience. `ROLE_*` → `role`, `ENABLE_*` → `enablement`.
- Enablement prerequisite relationships (e.g. `ENABLE_OPENAI` requires `ROLE_STORAGE`) are not stored in this table — they are enforced in the authorization module logic. This page defines what entries exist; the prerequisite graph is a separate concern.

## Description

Security entry management page. Defines roles (domain-level access) and enablements (subdomain/feature-level access) as GUID-keyed deterministic entries. Row-edit table for CRUD operations. Roles are tiered by audit level (user/admin/duty). Replaces the former bitmask-based role system with a named-entry model where GUIDs are derived from the role/enablement name string.