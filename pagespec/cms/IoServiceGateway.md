# TheOracleRPC — IoService Gateway & Session Architecture

## Design Document v0.13.0.0 (Revision 3)

**Status:** Proposal  
**Scope:** Greenfield — new tables, new schema, no FK references to legacy tables  
**Legacy bridge:** Existing `account_mcp_agents`, `account_mcp_agent_tokens`, `account_mcp_auth_codes`, `users_sessions`, `sessions_devices`, `account_api_tokens`, `users_auth`, `users_roles`, `users_enablements` are superseded. Existing code may temporarily read from both during migration.

---

## 1. Problem Statement

The application has multiple I/O gateways (RPC/HTTP, MCP, Discord) each implementing authentication, authorization, session management, and dispatch independently. The MCP gateway has a parallel JWT system (`mcp_gateway_module.py`) coupled to the legacy auth module. Discord resolves identity through its own lookup chain. The RPC router delegates to a handler that checks roles via a bitmask system on `users_roles.element_roles`.

The new security model (`system_users`, `system_auth_roles`, `system_user_roles`, `system_auth_entitlements`, `system_user_entitlements`, `service_auth_providers`, `system_user_auth`) introduced in v0.12.0–v0.12.2 is the correct foundation but has no session layer, no agent/client registration, no bearer token management, and no gateway registration in the object tree.

This design provides:

1. **Enumeration pattern** — deterministic lookup tables for all categorical values, registered in the object tree
2. **Session management** — unified sessions and bearer tokens for all gateways
3. **Agent/client registration** — data-driven client credentials replacing `account_mcp_agents`
4. **IoService gateway registry** — all gateways (including RPC) as object tree entries with method bindings
5. **UserContext contract** — the server-assembled identity+authz snapshot, encrypted in JWT, never exposing internal GUIDs to clients
6. **Compositional contracts** — shared interfaces for identity resolution, authorization, dispatch, and audit

---

## 2. Existing Foundation (What We Keep)

These tables from v0.12.0–v0.12.2 are canonical and unchanged:

| Table | Purpose | PK |
|---|---|---|
| `system_users` | Anchor identity | `key_guid` (UUID, NEWID()) |
| `service_auth_providers` | OAuth/OIDC provider config | `key_guid` (UUID5 from pub_name) |
| `system_user_auth` | User ↔ provider link mapping | `key_id` (BIGINT IDENTITY) |
| `system_auth_roles` | Role definitions | `key_guid` (UUID5 from pub_name) |
| `system_user_roles` | User ↔ role mapping | `key_guid` (UUID, NEWID()) |
| `system_auth_entitlements` | Entitlement definitions | `key_guid` (UUID5 from pub_name) |
| `system_user_entitlements` | User ↔ entitlement mapping | `key_guid` (UUID, NEWID()) |

These tables from v0.12.5.0 define the module and RPC namespace:

| Table | Purpose | PK |
|---|---|---|
| `system_objects_modules` | Server module registry | `key_guid` (UUID5) |
| `system_objects_module_methods` | Module method registry | `key_guid` (UUID5) |
| `system_objects_rpc_domains` | RPC domain (security boundary) | `key_guid` (UUID5) |
| `system_objects_rpc_subdomains` | RPC subdomain (feature group) | `key_guid` (UUID5) |
| `system_objects_rpc_functions` | RPC function (callable operation) | `key_guid` (UUID5) |

---

## 3. Enumeration Pattern

### Design Principle

All categorical/discriminator values use a unified two-table enumeration system rather than free-form strings or per-category lookup tables. This prevents instance drift across environments, makes the set of valid values discoverable in the object tree, and scales to any future enumeration without creating new tables.

### `service_enum_categories`

Registers each enumeration by name. One row per logical category.

```
service_enum_categories
├── key_guid         UNIQUEIDENTIFIER  NOT NULL  PK  (UUID5 from 'enum_category:{pub_name}')
├── pub_name         NVARCHAR(128)     NOT NULL  UNIQUE
├── pub_display      NVARCHAR(256)     NOT NULL
├── pub_description  NVARCHAR(512)     NULL
├── priv_created_on  DATETIMEOFFSET(7) NOT NULL  DEFAULT SYSUTCDATETIME()
├── priv_modified_on DATETIMEOFFSET(7) NOT NULL  DEFAULT SYSUTCDATETIME()
```

### `service_enum_values`

All enumeration values across all categories, FK'd to their parent category.

```
service_enum_values
├── key_guid              UNIQUEIDENTIFIER  NOT NULL  PK  (UUID5 from 'enum_value:{category_name}.{pub_name}')
├── ref_category_guid     UNIQUEIDENTIFIER  NOT NULL  FK → service_enum_categories.key_guid
├── pub_name              NVARCHAR(64)      NOT NULL
├── pub_display           NVARCHAR(128)     NOT NULL
├── pub_sequence          INT               NOT NULL  DEFAULT 0
├── priv_created_on       DATETIMEOFFSET(7) NOT NULL  DEFAULT SYSUTCDATETIME()
├── priv_modified_on      DATETIMEOFFSET(7) NOT NULL  DEFAULT SYSUTCDATETIME()
├── UNIQUE (ref_category_guid, pub_name)
```

All FK references from session, token, and gateway tables point to `service_enum_values.key_guid`. The FK constraint ensures valid values; the category grouping makes them browsable; the deterministic GUIDs prevent instance drift.

### Query Pattern

```sql
-- List all values in a category
SELECT v.pub_name, v.pub_display
FROM service_enum_values v
JOIN service_enum_categories c ON c.key_guid = v.ref_category_guid
WHERE c.pub_name = 'session_types'
ORDER BY v.pub_sequence;

-- Resolve a specific FK
SELECT v.pub_name FROM service_enum_values v WHERE v.key_guid = @ref_guid;
```

### Deterministic GUIDs

```python
NS = uuid.UUID('DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67')

# Categories
uuid5(NS, 'enum_category:session_types')
uuid5(NS, 'enum_category:token_types')
uuid5(NS, 'enum_category:gateway_transports')
uuid5(NS, 'enum_category:identity_strategies')

# Values
uuid5(NS, 'enum_value:session_types.browser')
uuid5(NS, 'enum_value:session_types.agent')
uuid5(NS, 'enum_value:session_types.bot')
uuid5(NS, 'enum_value:token_types.access')
uuid5(NS, 'enum_value:token_types.refresh')
uuid5(NS, 'enum_value:token_types.rotation')
# etc.
```

### Categories and Values Defined in This Design

**`session_types`** — Discriminator for `system_sessions.ref_session_type_guid`

| pub_name | pub_display | pub_sequence |
|---|---|---|
| `browser` | Web Browser Session | 10 |
| `agent` | MCP/API Agent Session | 20 |
| `bot` | Bot Service Session | 30 |

**`token_types`** — Discriminator for `system_session_tokens.ref_token_type_guid`

| pub_name | pub_display | pub_sequence |
|---|---|---|
| `access` | Access Token | 10 |
| `refresh` | Refresh Token | 20 |
| `rotation` | Rotation Token | 30 |

**`gateway_transports`** — Discriminator for `system_objects_io_gateways.ref_transport_guid`

| pub_name | pub_display | pub_sequence |
|---|---|---|
| `http_rpc` | HTTP RPC (POST /rpc) | 10 |
| `http_sse` | HTTP SSE (MCP Streamable) | 20 |
| `websocket` | WebSocket (Discord) | 30 |
| `http_rest` | HTTP REST API | 40 |
| `electron_ipc` | Electron IPC | 50 |

**`identity_strategies`** — Discriminator for `system_objects_gateway_identity_providers.ref_strategy_guid`

| pub_name | pub_display | pub_sequence |
|---|---|---|
| `bearer_jwt` | Bearer JWT Token | 10 |
| `static_token` | Static API Token | 20 |
| `discord_user_id` | Discord User ID | 30 |
| `api_key` | API Key | 40 |
| `client_credentials` | OAuth Client Credentials | 50 |

---

## 4. New Tables

### 4a. Session Layer

#### `system_sessions`

A session represents an authenticated context for a specific user. One user can have multiple concurrent sessions (one per device, one per agent client). Sessions are created on successful authentication and are the anchor for all bearer tokens.

```
system_sessions
├── key_guid                    UNIQUEIDENTIFIER  NOT NULL  PK  DEFAULT NEWID()
├── ref_user_guid               UNIQUEIDENTIFIER  NOT NULL  FK → system_users.key_guid
├── ref_session_type_guid       UNIQUEIDENTIFIER  NOT NULL  FK → service_enum_values.key_guid
├── pub_is_active               BIT               NOT NULL  DEFAULT 1
├── pub_revoked_at              DATETIMEOFFSET(7)  NULL
├── pub_expires_at              DATETIMEOFFSET(7)  NOT NULL
├── priv_created_on             DATETIMEOFFSET(7)  NOT NULL  DEFAULT SYSUTCDATETIME()
├── priv_modified_on            DATETIMEOFFSET(7)  NOT NULL  DEFAULT SYSUTCDATETIME()
```

**Notes:**
- Session type is FK to `service_enum_values` (category: `session_types`), not a free-form string.
- Session expiry is absolute. Token rotation happens within the session's lifetime.
- Revoking a session (`pub_revoked_at` set, `pub_is_active` = 0) invalidates all child tokens.

#### `system_session_tokens`

Bearer tokens issued within a session. Supports access/refresh/rotation token types. Multiple tokens can exist per session (token rotation creates new rows).

```
system_session_tokens
├── key_guid                    UNIQUEIDENTIFIER  NOT NULL  PK  DEFAULT NEWID()
├── ref_session_guid            UNIQUEIDENTIFIER  NOT NULL  FK → system_sessions.key_guid
├── ref_token_type_guid         UNIQUEIDENTIFIER  NOT NULL  FK → service_enum_values.key_guid
├── pub_token_hash              NVARCHAR(512)     NOT NULL  -- HMAC-SHA256 of token value
├── pub_scopes                  NVARCHAR(1024)    NULL
├── pub_issued_at               DATETIMEOFFSET(7)  NOT NULL  DEFAULT SYSUTCDATETIME()
├── pub_expires_at              DATETIMEOFFSET(7)  NOT NULL
├── pub_revoked_at              DATETIMEOFFSET(7)  NULL
├── priv_created_on             DATETIMEOFFSET(7)  NOT NULL  DEFAULT SYSUTCDATETIME()
```

**Token hashing:** Token values are never stored in plaintext. `pub_token_hash` contains an HMAC-SHA256 of the bearer token value, keyed with the same JWT secret from the environment variable. This provides:
- Constant-time comparison (HMAC vs raw SHA-256)
- Keyed hashing prevents rainbow table attacks against token hashes
- Consistent with JWT signing using the same key material
- No external dependency on bcrypt/argon2 libraries — reduces supply chain attack surface

The implementation must use `hmac.compare_digest()` for all hash comparisons to prevent timing attacks.

**Token cleanup requirements (document only, do not implement):**
- Expired tokens (`pub_expires_at < SYSUTCDATETIME()`) should be periodically purged
- Revoked tokens (`pub_revoked_at IS NOT NULL`) should be retained for audit trail for a configurable period (default: 90 days), then purged
- Cleanup should be a scheduled task registered in the automation system (`system_scheduled_tasks`), not an inline operation
- Cleanup must be idempotent and safe to run concurrently (DELETE with WHERE clause, no cursor loops)
- Suggested schedule: daily, during low-traffic window
- Cleanup should log the count of purged records to the audit trail

#### `system_session_devices`

Device/client metadata for a session. One row per session, captures fingerprint and network info.

```
system_session_devices
├── key_guid                    UNIQUEIDENTIFIER  NOT NULL  PK  DEFAULT NEWID()
├── ref_session_guid            UNIQUEIDENTIFIER  NOT NULL  FK → system_sessions.key_guid  UNIQUE
├── pub_device_fingerprint      NVARCHAR(512)     NULL
├── pub_user_agent              NVARCHAR(1024)    NULL
├── pub_ip_address              NVARCHAR(64)      NULL
├── pub_last_seen_at            DATETIMEOFFSET(7)  NULL
├── priv_created_on             DATETIMEOFFSET(7)  NOT NULL  DEFAULT SYSUTCDATETIME()
├── priv_modified_on            DATETIMEOFFSET(7)  NOT NULL  DEFAULT SYSUTCDATETIME()
```

### 4b. Agent/Client Registration

#### `service_agent_clients`

Registered API/MCP clients. Replaces `account_mcp_agents`. Follows the `service_*` naming convention for service-tier configuration.

```
service_agent_clients
├── key_guid                    UNIQUEIDENTIFIER  NOT NULL  PK  DEFAULT NEWID()
├── pub_client_id               UNIQUEIDENTIFIER  NOT NULL  UNIQUE  DEFAULT NEWID()
├── pub_client_name             NVARCHAR(256)     NOT NULL
├── pub_redirect_uris           NVARCHAR(MAX)     NULL
├── pub_grant_types             NVARCHAR(256)     NOT NULL  DEFAULT 'authorization_code'
├── pub_response_types          NVARCHAR(64)      NOT NULL  DEFAULT 'code'
├── pub_scopes                  NVARCHAR(1024)    NOT NULL  DEFAULT 'mcp:schema:read'
├── pub_is_dcr                  BIT               NOT NULL  DEFAULT 0
├── pub_is_active               BIT               NOT NULL  DEFAULT 1
├── pub_revoked_at              DATETIMEOFFSET(7)  NULL
├── pub_ip_address              NVARCHAR(64)      NULL
├── pub_user_agent              NVARCHAR(1024)    NULL
├── priv_created_on             DATETIMEOFFSET(7)  NOT NULL  DEFAULT SYSUTCDATETIME()
├── priv_modified_on            DATETIMEOFFSET(7)  NOT NULL  DEFAULT SYSUTCDATETIME()
```

**Notes:**
- `pub_client_id` is the value provided to external systems. The current `FA6CE2FC-784A-419A-BC43-B5F778161C9C` value becomes a seed row.
- `key_guid` is the internal PK for FK references. `pub_client_id` is the external-facing identifier, never used as FK.
- `pub_is_dcr` tracks whether this client was auto-created via Dynamic Client Registration vs manually provisioned.
- No user FK here — the user-to-client link is expressed through `service_agent_client_users`.

**Known agent scenarios and requirements:**

| Agent | Auth Method | Status | Notes |
|---|---|---|---|
| Claude.ai (MCP) | OAuth PKCE via `pub_client_id` | Working | Static client registration, redirect to `/api/mcp/auth_callback`, consent page links to identity provider login |
| Codex Cloud (MCP) | `.codex/config.toml` with credentials | Blocked | Requires `client_credentials` grant type support — no interactive browser flow available. Server must support `grant_type=client_credentials` on the token endpoint, returning tokens without user consent UI. |
| Copilot Studio (MCP) | DCR + OAuth | Previously tested | DCR was enabled, Copilot Studio dynamically registered a client and completed OAuth flow. DCR is currently disabled by design. When enabled, writes to `service_agent_clients` with `pub_is_dcr = 1`. Additional OAuth configuration options in Copilot Studio (static bearer tokens, custom headers) were not fully explored. |
| Future REST API clients | API key or Bearer JWT | Planned | Simple bearer token auth — most straightforward IoService pattern. Client presents token, server resolves to session/identity. |
| Future Electron app | Same as browser RPC | Planned | Electron wraps the React app; auth flows are identical to browser. `electron_ipc` transport registered for future native IPC needs. |

The `pub_grant_types` column must support `authorization_code` (interactive OAuth), `client_credentials` (non-interactive machine-to-machine), and potentially `refresh_token` as grant types. The token endpoint must dispatch based on the `grant_type` parameter in the request.

#### `service_agent_client_users`

Maps agent clients to authorized users. A client can be linked to multiple users (multi-tenant agent), a user can have multiple clients.

```
service_agent_client_users
├── key_guid                    UNIQUEIDENTIFIER  NOT NULL  PK  DEFAULT NEWID()
├── ref_client_guid             UNIQUEIDENTIFIER  NOT NULL  FK → service_agent_clients.key_guid
├── ref_user_guid               UNIQUEIDENTIFIER  NOT NULL  FK → system_users.key_guid
├── pub_is_active               BIT               NOT NULL  DEFAULT 1
├── priv_created_on             DATETIMEOFFSET(7)  NOT NULL  DEFAULT SYSUTCDATETIME()
├── priv_modified_on            DATETIMEOFFSET(7)  NOT NULL  DEFAULT SYSUTCDATETIME()
├── UNIQUE (ref_client_guid, ref_user_guid)
```

#### `service_agent_auth_codes`

OAuth authorization codes for the PKCE flow. Short-lived, consumed once. Replaces `account_mcp_auth_codes`.

```
service_agent_auth_codes
├── key_guid                    UNIQUEIDENTIFIER  NOT NULL  PK  DEFAULT NEWID()
├── ref_client_guid             UNIQUEIDENTIFIER  NOT NULL  FK → service_agent_clients.key_guid
├── ref_user_guid               UNIQUEIDENTIFIER  NOT NULL  FK → system_users.key_guid
├── pub_code                    NVARCHAR(256)     NOT NULL
├── pub_code_challenge          NVARCHAR(256)     NOT NULL
├── pub_code_method             NVARCHAR(16)      NOT NULL  DEFAULT 'S256'
├── pub_redirect_uri            NVARCHAR(2048)    NOT NULL
├── pub_scopes                  NVARCHAR(1024)    NOT NULL
├── pub_consumed                BIT               NOT NULL  DEFAULT 0
├── pub_expires_at              DATETIMEOFFSET(7)  NOT NULL
├── priv_created_on             DATETIMEOFFSET(7)  NOT NULL  DEFAULT SYSUTCDATETIME()
```

**Auth code cleanup requirements (document only, do not implement):**
- Expired and unconsumed codes (`pub_expires_at < SYSUTCDATETIME() AND pub_consumed = 0`) should be purged periodically
- Consumed codes (`pub_consumed = 1`) should be retained for audit trail for a configurable period (default: 30 days), then purged
- Cleanup cadence: daily, same scheduled task as token cleanup
- Auth codes have a very short TTL (60 seconds), so the cleanup window is generous

### 4c. IoService Gateway Registry

#### Design Principle: RPC is the Canonical Gateway

Every external interaction with the system — whether from a React browser app, an MCP agent, a Discord bot, a REST API client, or a future Electron app — is an IoService gateway. The RPC/HTTP gateway (`POST /rpc`) is not a special case; it is the **baseline canonical pattern** from which all others derive.

The existing RPC flow established in `rpc/helpers.py` → `unbox_request()` defines the security contract:

1. **Transport receives raw request** (HTTP POST body, MCP tool call, Discord message, etc.)
2. **Identity resolution:** Extract credentials from transport (bearer token from `Authorization` header, Discord user ID from message context, static token from env var). Decode/validate. Resolve to `system_users.key_guid`.
3. **AuthContext assembly:** Look up user's roles (`system_user_roles` → `system_auth_roles`) and entitlements (`system_user_entitlements` → `system_auth_entitlements`). Build `AuthContext` with user_guid, role list, and role mask.
4. **Authorization check:** Verify the resolved identity has the required role for the target domain and entitlement for the target subdomain.
5. **Dispatch:** Route to the correct module method via the FK chain (function → method → module → `app.state.{attr}`).
6. **Response packaging:** Module returns typed Pydantic model. Gateway serializes and returns via transport.

Every IoService gateway implements this same six-step flow. The differences are only in step 1 (transport-specific credential extraction) and step 6 (transport-specific response serialization). Steps 2–5 are shared contracts.

#### `system_objects_io_gateways`

Registers each I/O gateway as an object tree entry.

```
system_objects_io_gateways
├── key_guid                    UNIQUEIDENTIFIER  NOT NULL  PK  (UUID5)
├── pub_name                    NVARCHAR(128)     NOT NULL  UNIQUE
├── ref_transport_guid          UNIQUEIDENTIFIER  NOT NULL  FK → service_enum_values.key_guid
├── pub_description             NVARCHAR(512)     NULL
├── ref_module_guid             UNIQUEIDENTIFIER  NOT NULL  FK → system_objects_modules.key_guid
├── pub_is_active               BIT               NOT NULL  DEFAULT 1
├── priv_created_on             DATETIMEOFFSET(7)  NOT NULL  DEFAULT SYSUTCDATETIME()
├── priv_modified_on            DATETIMEOFFSET(7)  NOT NULL  DEFAULT SYSUTCDATETIME()
```

**Seed data:**

| pub_name | transport (FK) | module (FK) | Notes |
|---|---|---|---|
| `rpc` | `http_rpc` | RpcIoServiceModule | The canonical baseline. Browser React app, any HTTP client. |
| `mcp` | `http_sse` | McpIoServiceModule | MCP Streamable HTTP for Claude, Codex, Copilot Studio. |
| `discord` | `websocket` | DiscordIoServiceModule | Discord gateway bot. |
| `api` | `http_rest` | ApiIoServiceModule | Future REST API for external integrations. |

#### `system_objects_gateway_identity_providers`

Defines which identity resolution strategies a gateway supports. A gateway may support multiple strategies (e.g., MCP supports both static token and OAuth JWT; RPC supports bearer JWT and Discord user ID).

```
system_objects_gateway_identity_providers
├── key_guid                    UNIQUEIDENTIFIER  NOT NULL  PK  (UUID5)
├── ref_gateway_guid            UNIQUEIDENTIFIER  NOT NULL  FK → system_objects_io_gateways.key_guid
├── ref_strategy_guid           UNIQUEIDENTIFIER  NOT NULL  FK → service_enum_values.key_guid
├── pub_priority                INT               NOT NULL  DEFAULT 0
├── pub_description             NVARCHAR(512)     NULL
├── pub_is_active               BIT               NOT NULL  DEFAULT 1
├── priv_created_on             DATETIMEOFFSET(7)  NOT NULL  DEFAULT SYSUTCDATETIME()
├── priv_modified_on            DATETIMEOFFSET(7)  NOT NULL  DEFAULT SYSUTCDATETIME()
├── UNIQUE (ref_gateway_guid, ref_strategy_guid)
```

**Seed data:**

| gateway | strategy | priority | Notes |
|---|---|---|---|
| rpc | `bearer_jwt` | 10 | Primary: session JWT from browser login |
| rpc | `discord_user_id` | 20 | Secondary: Discord domain requests with `x-discord-id` header |
| mcp | `static_token` | 10 | Primary: `MCP_AGENT_TOKEN` env var for dev/admin |
| mcp | `bearer_jwt` | 20 | Secondary: OAuth PKCE JWT for Claude.ai |
| mcp | `client_credentials` | 30 | Tertiary: machine-to-machine for Codex |
| discord | `discord_user_id` | 10 | Discord message author → provider link |
| api | `api_key` | 10 | Future: static API key |
| api | `bearer_jwt` | 20 | Future: OAuth JWT |

#### `system_objects_gateway_method_bindings`

Maps gateway-specific operations to module methods. For RPC, each URN operation becomes a row. For MCP, each tool becomes a row. For Discord, each command becomes a row. This replaces the hardcoded tool definitions in `mcp_server.py` and eventually the hardcoded `DISPATCHERS` dicts in RPC subdomains.

```
system_objects_gateway_method_bindings
├── key_guid                    UNIQUEIDENTIFIER  NOT NULL  PK  (UUID5)
├── ref_gateway_guid            UNIQUEIDENTIFIER  NOT NULL  FK → system_objects_io_gateways.key_guid
├── ref_method_guid             UNIQUEIDENTIFIER  NOT NULL  FK → system_objects_module_methods.key_guid
├── pub_operation_name          NVARCHAR(128)     NOT NULL
├── pub_description             NVARCHAR(512)     NULL
├── pub_required_scope          NVARCHAR(128)     NULL
├── ref_required_role_guid      UNIQUEIDENTIFIER  NULL      FK → system_auth_roles.key_guid
├── ref_required_entitlement_guid UNIQUEIDENTIFIER NULL     FK → system_auth_entitlements.key_guid
├── pub_is_read_only            BIT               NOT NULL  DEFAULT 1
├── pub_is_active               BIT               NOT NULL  DEFAULT 1
├── priv_created_on             DATETIMEOFFSET(7)  NOT NULL  DEFAULT SYSUTCDATETIME()
├── priv_modified_on            DATETIMEOFFSET(7)  NOT NULL  DEFAULT SYSUTCDATETIME()
├── UNIQUE (ref_gateway_guid, pub_operation_name)
```

**Notes:**
- The same module method can be exposed through multiple gateways with different operation names and different security requirements.
- For RPC, `pub_operation_name` is the full URN: `urn:public:route:load_shell:1`.
- For MCP, `pub_operation_name` is the tool name: `oracle_list_tables`.
- For Discord, `pub_operation_name` is the command: `!persona`.
- `pub_required_scope` is transport-specific (MCP scopes like `mcp:schema:read`). Role and entitlement FKs are universal security checks.

---

## 5. Authentication & Authorization Flow

### Critical Security Principle: No Internal GUIDs to Clients

The user's `system_users.key_guid` is **never sent to any client**. The frontend receives an encrypted JWT containing the user's context. The JWT is signed and encrypted with the server's `JWT_SECRET` environment variable (configured directly on the web server as critical infrastructure).

What the client receives:
- **Session JWT** — encrypted, contains user context claims (display name, roles, entitlements, session type). Sent as bearer token in `Authorization` header on every RPC request.
- **Rotation token** — long-lived, used for silent re-auth. Stored in HTTP-only cookie.

What the client never receives:
- `system_users.key_guid`
- `system_sessions.key_guid`
- Role GUIDs, entitlement GUIDs, or any internal FK values

### Token Issuance Flow (Preserving Current Patterns)

Reference: `AUTHENTICATION_DIAGRAMS.md` — Session Token Issuance

```
Client → POST /rpc { op: "urn:public:auth:session:get_token:1", payload: { provider, tokens, fingerprint } }
  → RPC Layer: unbox_request() — no bearer token required for auth domain
  → SessionModule.issue_token(provider, tokens, fingerprint)
    → AuthModule.handle_auth_login(provider, id_token, access_token)
      → AuthProviderBase.verify_id_token() — validates with provider JWKS
      → AuthProviderBase.fetch_user_profile() — gets provider profile
    → OauthModule.resolve_user(...)
      → DB: create_from_provider / link / relink in system_user_auth
      → Creates system_sessions row (type = 'browser')
      → Creates system_session_tokens rows (access + refresh + rotation)
      → Creates system_session_devices row
    → AuthModule.make_session_token(user_guid, roles, entitlements, session_type)
      → JWT contains: { sub: <encrypted_ref>, roles: [...], entitlements: [...], session_type, exp, iat }
      → JWT signed with JWT_SECRET (env var, never in database)
  ← RPCResponse { session_token, rotation_cookie (HTTP-only), profile (display, email, roles) }
```

### Token Refresh Flow

Reference: `AUTHENTICATION_DIAGRAMS.md` — Session Token Refresh

```
Client → POST /rpc { op: "urn:public:auth:session:refresh_token:1" } + rotation cookie
  → SessionModule.refresh_token(rotation_token, fingerprint)
    → Validate rotation token hash against system_session_tokens
    → Verify session is active, not expired, not revoked
    → Look up user roles and entitlements from mapping tables
    → Issue new access token → system_session_tokens row
    → Update system_session_devices.pub_last_seen_at
  ← RPCResponse { new session_token }
```

### Bearer Token Resolution (All Gateways)

This is the core of `unbox_request()` — the pattern every gateway follows:

```
1. Extract credentials from transport:
   - RPC: Authorization header → bearer JWT
   - MCP: Authorization header → static token OR bearer JWT
   - Discord: Message context → discord user ID
   - API: X-API-Key header OR Authorization header

2. Resolve identity:
   IF bearer JWT:
     → Decode JWT with JWT_SECRET
     → Extract sub claim → internal user reference
     → Verify token hash exists in system_session_tokens and is not expired/revoked
     → Verify parent session is active
   IF static token:
     → Compare against MCP_AGENT_TOKEN env var (HMAC comparison)
     → Resolve to pre-configured admin identity
   IF discord user ID:
     → Look up system_user_auth WHERE ref_provider_guid = discord_provider AND pub_provider_identifier = discord_id
     → Resolve to system_users.key_guid
   IF client_credentials:
     → Validate client_id + client_secret against service_agent_clients
     → Resolve linked user from service_agent_client_users
   IF api_key:
     → Hash provided key, look up in system_session_tokens

3. Assemble AuthContext (server-side only, never transmitted):
   AuthContext {
     user_guid: str        — system_users.key_guid
     roles: list[str]      — role names from system_user_roles → system_auth_roles
     role_mask: int         — bitmask for fast bitwise checks (legacy compat, transitional)
     entitlements: list[str] — from system_user_entitlements → system_auth_entitlements
     session_guid: str     — system_sessions.key_guid
     session_type: str     — from service_enum_values (category: session_types)
     scopes: set[str]      — transport-specific scopes from token
     provider: str         — identity strategy that resolved
     claims: dict          — raw JWT claims (if applicable)
   }

4. Authorize:
   → Check domain role: operation.ref_required_role_guid ∈ user's role GUIDs
   → Check subdomain entitlement: operation.ref_required_entitlement_guid ∈ user's entitlement GUIDs
   → Check transport scope: operation.pub_required_scope ∈ session scopes

5. Dispatch:
   → gateway_method_binding.ref_method_guid → module_method → module → app.state.{attr}
   → Call module.method(auth_ctx, payload)

6. Response:
   → Module returns Pydantic model
   → Gateway serializes per transport (JSON for RPC/API, tool result for MCP, message for Discord)
```

### UserContext (Frontend Contract)

The UserContext is what the frontend React app receives — it is the **decrypted and filtered** subset of the AuthContext that is safe to expose. It is an RPC model registered in `system_objects_rpc_models`.

**Model: `UserContext1`** (registered in system_objects_rpc_models)

| Field | Type | Nullable | Source |
|---|---|---|---|
| `display` | STRING | no | `system_users.pub_display` |
| `email` | STRING | no | `system_users.pub_email` |
| `roles` | list[STRING] | no | Role names from `system_user_roles` → `system_auth_roles.pub_name` |
| `entitlements` | list[STRING] | no | Entitlement names from `system_user_entitlements` → `system_auth_entitlements.pub_name` |
| `providers` | list[STRING] | no | Linked provider names from `system_user_auth` → `service_auth_providers.pub_name` |
| `sessionType` | STRING | no | From `service_enum_values.pub_name` (category: session_types) |
| `isAuthenticated` | BOOL | no | Convenience flag |

**What is NOT in UserContext:** No GUIDs. No internal IDs. No session keys. No token hashes. The frontend knows the user's display name, email, what they're allowed to do (roles/entitlements), how they logged in (providers), and what kind of session they have. That's it.

**Frontend consumption:**
- Client calls `urn:public:auth:get_user_context:1` on app load (bearer token in header)
- Server decodes JWT → resolves AuthContext → projects to UserContext1 → returns
- React `UserContextProvider` stores the result
- Components read from context: `if (userContext.roles.includes('ROLE_SERVICE_ADMIN'))` for conditional rendering
- The TypeScript interface is auto-generated from the RPC model definition via `generate_rpc_bindings.py`

---

## 6. Compositional Contracts

These are Python protocol classes that IoService gateway modules compose. Each contract defines a single responsibility.

### 6a. IdentityResolver

```python
class ResolvedIdentity(BaseModel):
    user_guid: str                    # system_users.key_guid — NEVER leaves the server
    session_guid: str | None          # system_sessions.key_guid
    roles: list[str]                  # role GUIDs from system_user_roles
    entitlements: list[str]           # entitlement GUIDs from system_user_entitlements
    scopes: set[str]                  # transport-specific scopes from token
    source: str                       # identity strategy name

class IdentityResolver(Protocol):
    async def resolve(self, transport_credentials: Any) -> ResolvedIdentity | None: ...
```

Each gateway has its own IdentityResolver implementation that chains through strategies defined in `system_objects_gateway_identity_providers`, ordered by `pub_priority`. First successful resolution wins.

### 6b. AuthzGate

```python
class AuthzGate(Protocol):
    async def check(self, identity: ResolvedIdentity, binding: GatewayMethodBinding) -> bool: ...
```

Shared implementation, not per-gateway. Checks:
1. Transport scope: `binding.pub_required_scope` ∈ `identity.scopes`
2. Role: `binding.ref_required_role_guid` ∈ `identity.roles` (NULL = no role required)
3. Entitlement: `binding.ref_required_entitlement_guid` ∈ `identity.entitlements` (NULL = no entitlement required)

All applicable checks must pass.

### 6c. ModuleDispatch

```python
class ModuleDispatch(Protocol):
    async def dispatch(self, binding: GatewayMethodBinding, auth_ctx: AuthContext, payload: dict) -> Any: ...
```

Resolution chain:
1. `binding.ref_method_guid` → `system_objects_module_methods.key_guid`
2. `module_method.ref_module_guid` → `system_objects_modules.pub_state_attr`
3. `app.state.{pub_state_attr}` → module instance
4. `getattr(module, method.pub_name)` → callable
5. Call with `auth_ctx` and payload

### 6d. AuditEmitter

```python
class AuditEmitter(Protocol):
    async def emit(self, level: str, gateway: str, operation: str,
                   identity: ResolvedIdentity | None, message: str) -> None: ...
```

Shared implementation. Writes to structured log and optionally to Discord system channel.

---

## 7. FK Graph

```
service_enum_categories
  (standalone — defines enum groupings)

service_enum_values
  └── ref_category_guid → service_enum_categories.key_guid
  ← system_sessions.ref_session_type_guid
  ← system_session_tokens.ref_token_type_guid
  ← system_objects_io_gateways.ref_transport_guid
  ← system_objects_gateway_identity_providers.ref_strategy_guid

system_sessions
  ├── ref_user_guid → system_users.key_guid
  └── ref_session_type_guid → service_enum_values.key_guid

system_session_tokens
  ├── ref_session_guid → system_sessions.key_guid
  └── ref_token_type_guid → service_enum_values.key_guid

system_session_devices
  └── ref_session_guid → system_sessions.key_guid (UNIQUE)

service_agent_clients
  (no FK — standalone registry)

service_agent_client_users
  ├── ref_client_guid → service_agent_clients.key_guid
  └── ref_user_guid → system_users.key_guid

service_agent_auth_codes
  ├── ref_client_guid → service_agent_clients.key_guid
  └── ref_user_guid → system_users.key_guid

system_objects_io_gateways
  ├── ref_transport_guid → service_enum_values.key_guid
  └── ref_module_guid → system_objects_modules.key_guid

system_objects_gateway_identity_providers
  ├── ref_gateway_guid → system_objects_io_gateways.key_guid
  └── ref_strategy_guid → service_enum_values.key_guid

system_objects_gateway_method_bindings
  ├── ref_gateway_guid → system_objects_io_gateways.key_guid
  ├── ref_method_guid → system_objects_module_methods.key_guid
  ├── ref_required_role_guid → system_auth_roles.key_guid (nullable)
  └── ref_required_entitlement_guid → system_auth_entitlements.key_guid (nullable)
```

---

## 8. Discord Table Updates

The existing `discord_guilds` and `discord_channels` tables use legacy conventions (`recid` PKs, `element_*` columns). These should be replaced:

| Legacy | New | Notes |
|---|---|---|
| `discord_guilds` | `service_discord_guilds` | `key_guid` PK (UUID5 from guild_id), `pub_*` columns |
| `discord_channels` | `service_discord_channels` | `key_guid` PK (UUID5 from channel_id), FK to `service_discord_guilds.key_guid` |

These follow the `service_*` convention for external integration configuration. Full column definitions deferred to implementation phase.

---

## 9. Rate Limiting

The current `SlidingWindowRateLimiter` in `mcp_gateway_module.py` is in-memory. Configuration values (`MCP_RATE_LIMIT_REGISTER_IP`, etc.) are stored in `system_config`.

For the new design, rate limit configuration should move to the object tree. The specific location is TBD — likely a configuration node on each gateway registration or a dedicated `system_objects_gateway_rate_limits` table. The in-memory sliding window implementation is appropriate for single-instance deployment; a Redis-backed implementation is a natural future extension.

---

## 10. Scope Definitions

MCP scopes (`mcp:schema:read`, `mcp:data:read`, etc.) and future API scopes should be registered in the object tree. Scopes are related to but distinct from entitlements:

- **Entitlements** gate access to system features (e.g., `ENABLE_DISCORD_BOT` enables the Discord feature for a user)
- **Scopes** constrain what a specific token can do within an already-entitled feature (e.g., an MCP token with `mcp:schema:read` can read schema but not write data, even if the user has full entitlements)

Scopes are a refinement layer on top of entitlements: the user must have the entitlement AND the token must have the scope. This maps to credit consumption in the financial system — scope checks happen at the same layer as credit deduction.

The specific table structure and object tree location for scope definitions is deferred to implementation. The current free-form string approach in `pub_scopes` columns is functional but should be backed by a lookup table for consistency with the enumeration pattern.

---

## 11. Legacy Mapping

| Legacy table | New table | Migration notes |
|---|---|---|
| `account_mcp_agents` | `service_agent_clients` + `service_agent_client_users` | Copy `element_client_id` → `pub_client_id`, create user link row |
| `account_mcp_agent_tokens` | `system_session_tokens` | Create `system_sessions` per active token set, hash access tokens |
| `account_mcp_auth_codes` | `service_agent_auth_codes` | Direct column mapping, FK to new tables |
| `users_sessions` | `system_sessions` | `element_guid` → `key_guid`, type = browser |
| `sessions_devices` | `system_session_devices` + `system_session_tokens` | Split: device metadata → devices, tokens → tokens |
| `account_api_tokens` | `service_agent_clients` + `system_session_tokens` | Each API token → client + session + token |
| `discord_guilds` | `service_discord_guilds` | Re-key to UUID5, rename columns |
| `discord_channels` | `service_discord_channels` | Re-key to UUID5, FK to new guilds table |

---

## 12. Server Module Changes

### New modules to register in `system_objects_modules`:

| pub_name | pub_state_attr | pub_module_path |
|---|---|---|
| `RpcIoServiceModule` | `rpc_io` | `server.modules.rpc_io_service_module` |
| `McpIoServiceModule` | `mcp_io` | `server.modules.mcp_io_service_module` |
| `DiscordIoServiceModule` | `discord_io` | `server.modules.discord_io_service_module` |

The existing `SessionModule` will be rewritten against the new tables. The existing `McpGatewayModule` and `mcp_server.py` tool definitions are replaced by `McpIoServiceModule`. The existing `DiscordBotModule` transport code stays; identity/auth/dispatch moves to compositional contracts.

### Module startup dependency order:

```
EnvModule → DbModule → RoleModule → SessionModule → AuthModule
  → RpcIoServiceModule (canonical baseline)
  → McpIoServiceModule
  → DiscordIoServiceModule
```

Each IoService module on startup:
1. Reads its gateway registration from `system_objects_io_gateways`
2. Loads identity provider strategies from `system_objects_gateway_identity_providers`
3. Loads method bindings from `system_objects_gateway_method_bindings`
4. Registers transport-specific endpoints

---

## 13. Object Tree Self-Registration

All new tables (2 enum + 3 session + 3 agent + 3 gateway + 2 Discord = 13 tables) must be registered in `system_objects_database_tables` with full column, index, and constraint seed data. Deterministic UUID5 formulas:

```python
import uuid
NS = uuid.UUID('DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67')

# Enum system
uuid.uuid5(NS, 'table:service_enum_categories')
uuid.uuid5(NS, 'table:service_enum_values')

# Session tables
uuid.uuid5(NS, 'table:system_sessions')
uuid.uuid5(NS, 'table:system_session_tokens')
uuid.uuid5(NS, 'table:system_session_devices')

# Agent tables
uuid.uuid5(NS, 'table:service_agent_clients')
uuid.uuid5(NS, 'table:service_agent_client_users')
uuid.uuid5(NS, 'table:service_agent_auth_codes')

# Gateway tables
uuid.uuid5(NS, 'table:system_objects_io_gateways')
uuid.uuid5(NS, 'table:system_objects_gateway_identity_providers')
uuid.uuid5(NS, 'table:system_objects_gateway_method_bindings')

# Discord tables
uuid.uuid5(NS, 'table:service_discord_guilds')
uuid.uuid5(NS, 'table:service_discord_channels')

# Enum categories: uuid.uuid5(NS, 'enum_category:{category_name}')
# Enum values: uuid.uuid5(NS, 'enum_value:{category_name}.{value_name}')
# Columns: uuid.uuid5(NS, 'column:{table_name}.{column_name}')
# Gateways: uuid.uuid5(NS, 'gateway:{pub_name}')
# Modules: uuid.uuid5(NS, '{ModuleClassName}')
```

---

## 14. Implementation Sequence

### Phase 1: Schema (migration SQL)
1. Create `service_enum_categories` and `service_enum_values` tables
2. Seed enum categories (session_types, token_types, gateway_transports, identity_strategies)
3. Seed enum values for all categories
4. Create session tables with FK to `service_enum_values`
5. Create agent/client tables
6. Create gateway registry tables with FK to `service_enum_values`
7. Create Discord replacement tables
8. Self-register all 13 tables in object tree
9. Seed gateway registrations, identity provider strategies
10. Seed `FA6CE2FC` client in `service_agent_clients`
11. Register `UserContext1` model in `system_objects_rpc_models/model_fields`
12. Register new modules in `system_objects_modules`

### Phase 2: Session module rewrite
1. Rewrite `SessionModule` against new tables
2. Implement HMAC-SHA256 token hashing with `hmac.compare_digest()`
3. Implement token creation, validation, refresh, revocation
4. Implement `get_user_context()` → assembles `UserContext1` (no GUIDs in output)
5. Preserve rotation token → HTTP-only cookie pattern from legacy

### Phase 3: RPC gateway formalization
1. Create `RpcIoServiceModule` wrapping existing `rpc/handler.py` + `rpc/helpers.py`
2. Load method bindings from `system_objects_gateway_method_bindings` on startup
3. Refactor `unbox_request()` to use composed IdentityResolver
4. This is the canonical reference implementation — all other gateways mirror it

### Phase 4: MCP gateway
1. Create `McpIoServiceModule` composing IdentityResolver + AuthzGate + ModuleDispatch + AuditEmitter
2. Generate MCP tool registrations dynamically from bindings
3. Implement `client_credentials` grant type for Codex support
4. Wire into lifespan replacing current `mcp_server.py` + `mcp_gateway_module.py`

### Phase 5: Discord gateway
1. Create `DiscordIoServiceModule` wrapping existing Discord.py transport
2. Implement Discord-specific IdentityResolver
3. Migrate guild/channel data to new tables

### Phase 6: Frontend UserContext
1. Add `UserContextProvider` to client App.tsx
2. Call `get_user_context` on load with bearer token
3. Wire NavigationSidebar route filtering to role checks
4. Wire DevModeToggle visibility to `ROLE_SERVICE_ADMIN`

### Phase 7: Legacy cleanup
1. Stop writing to legacy auth/session tables
2. Remove legacy QueryRegistry namespaces
3. Drop legacy tables (deferred until stable)

---

## 15. Data-Driven Module Code (Future Vision)

The compositional pattern positions the system for a future where module implementations are stored in the database. The progression:

1. **Today:** Module Python files on disk, registered in `system_objects_modules` by path
2. **Near-term:** Module code synced to a `system_objects_module_source` table alongside the file
3. **Mid-term:** Database becomes canonical source; files generated as build artifacts
4. **Long-term:** Runtime executor loads module code from database blobs, `exec()` in sandboxed namespace, hot-reload on row change

The gateway method bindings already decouple "what operation exists" from "what code implements it." Once module source code is also data, the entire application is a database restore.

---

## 16. Design Decisions Record

| Decision | Choice | Rationale |
|---|---|---|
| JWT signing key | Environment variable (`JWT_SECRET`) | Critical infrastructure, configured directly on web server. Never stored in database. |
| Token hashing | HMAC-SHA256 keyed with JWT_SECRET | Constant-time comparison, keyed hash prevents rainbow tables, no external crypto library dependency reduces supply chain risk. |
| Enumeration pattern | Unified `service_enum_categories` + `service_enum_values` with UUID5 PKs | Two tables handle all enumerations. Prevents instance drift, FK constraints enforce validity, scales without creating new tables. |
| RPC as gateway | RPC is a registered IoService gateway, not special-cased | All gateways follow the same six-step security flow. RPC is the canonical baseline. |
| User GUID exposure | Never sent to any client | Clients receive encrypted JWT. Internal identity stays server-side. UserContext contains display values only. |
| Scope definitions | Deferred, placeholder free-form strings | Relationship to entitlements and credit consumption needs further design. Object tree location TBD. |
| Rate limiting storage | In-memory for now, config in object tree | Single-instance sufficient. Redis extension natural when needed. |