# Input Shim Architecture

This document describes the **input shim pattern** used by TheOracleRPC to
connect external protocols to the platform's RPC layer.

## Design Principle

An input shim is a thin protocol adapter that:

1. **Receives** requests from an external protocol (HTTP, WebSocket, AT
   Protocol, MCP, etc.).
2. **Authenticates** the caller using the protocol's native auth mechanism.
3. **Resolves** the caller to an internal user GUID and role bitmask.
4. **Constructs** an `RPCRequest` with the resolved auth context.
5. **Dispatches** through `dispatch_rpc_op()` — the same entry point used by
   all callers.
6. **Returns** the `RPCResponse` payload translated to the protocol's response
   format.

Input shims contain **no business logic**. They are structurally equivalent to
the FastAPI RPC router (`server/routers/rpc_router.py`) — receive,
authenticate, dispatch, return. All validation, authorization, and execution
happens in the RPC → Module → Provider chain.

## Why This Matters

Every input surface — React frontend, Discord bot, TheOracleMCP, social media
bridges — is a different view into the same authoritative backend. By routing
all of them through the RPC boundary:

- Security is enforced uniformly (role bitmask, entitlements, credits).
- Business logic exists in exactly one place (modules).
- New input surfaces require only a protocol adapter, not new business logic.
- Testing covers the real code path regardless of which surface triggered it.

## Implementation Pattern

### Module Structure

Input shims follow the `SocialInputModule` / `SocialInputProvider` pattern:

- A **coordinator module** (`SocialInputModule`) manages provider lifecycle.
- Each protocol has a **provider** (e.g. `DiscordInputProvider`) that
  implements the protocol-specific adapter.
- Providers register with the coordinator at startup and deregister at
  shutdown.

### Auth Resolution

Each shim resolves its protocol-specific identity to the platform's internal
auth model:

| Surface | Identity Source | Resolution Path |
|---------|----------------|-----------------|
| React frontend | Bearer token in `Authorization` header | `AuthModule.decode_session_token()` → GUID, roles, mask |
| Discord | Discord user ID from message context | `AuthModule.get_discord_user_security()` → GUID, roles, mask |
| TheOracleMCP (target) | OAuth 2.1 JWT in `Authorization` header | Decode JWT → `sub` (GUID) → `AuthModule.get_user_roles()` → roles, mask |
| Social integrations (planned) | Platform-specific identity | Platform ID → linked provider → GUID resolution |

### Dispatch

All shims call `dispatch_rpc_op()` from `rpc/handler.py`:

```python
response = await dispatch_rpc_op(
    app,
    "urn:domain:subsystem:operation:version",
    payload_dict,
    discord_ctx=metadata,  # or equivalent context for other shims
)
```

The `dispatch_rpc_op` function builds a request object with the auth context
and delegates to the domain handler. The exact parameter shape may evolve as
new shims are added, but the contract is the same: the shim provides identity,
the RPC layer enforces authorization.

## Current Input Surfaces

### React Frontend (Production)

- **Entry:** `POST /rpc` → `rpc_router.py` → `handle_rpc_request()`
- **Auth:** Bearer token → `_process_rpcrequest()` →
  `AuthModule.decode_session_token()`
- **Pattern:** Direct HTTP RPC. The frontend sends
  `{ op: "urn:...", payload: {...} }`.

### Discord (Production)

- **Entry:** Discord WebSocket → `discord.py` bot →
  `DiscordInputProvider`
- **Auth:** Discord user ID → `AuthModule.get_discord_user_security()` →
  GUID, roles
- **Pattern:** Bot commands (`!summarize`, `!persona`, `!credits`,
  `!guildcredits`) translated to RPC calls via
  `dispatch_rpc_op()`.
- **Files:** `server/modules/social_input_module.py`,
  `server/modules/providers/social/discord_input_provider.py`

### TheOracleMCP (Production path, iterative hardening)

- **Entry:** Streamable HTTP `/mcp` → MCP SDK → tool functions in
  `mcp_server.py`
- **Auth (current):** Static token or OAuth JWT → scope check in tool
  functions → role resolution (`AuthModule.get_user_roles()` for OAuth users,
  `ROLE_SERVICE_ADMIN` mask for static token).
- **Pattern (current):** Tools call `dispatch_rpc_op()` with
  `urn:service:reflection:*` operations under `ROLE_SERVICE_ADMIN` semantics.
- **Files:** `server/mcp_server.py`, `server/routers/mcp_router.py`,
  `server/modules/mcp_gateway_module.py`, `server/routers/oauth_router.py`

### Social Integrations (Planned)

- **Targets:** Bluesky, TikTok, and others as platform APIs allow.
- **Pattern:** Same shim architecture — platform-specific adapter,
  identity resolution to internal GUID, dispatch through RPC.
- **Files:** `server/modules/bsky_module.py` (exists, early stage)

## Constraints

- Input shims MUST NOT contain business logic.
- Input shims MUST NOT call QueryRegistry directly — all data access goes
  through the RPC → Module → Provider chain.
- Input shims MUST resolve protocol identity to internal GUID + role bitmask
  before dispatching.
- Input shims MUST use `dispatch_rpc_op()` as the sole dispatch entry point.
- New input surfaces SHOULD follow the `SocialInputModule` / provider pattern
  for lifecycle management.
