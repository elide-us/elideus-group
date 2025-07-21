# Security Roles and Capability Masks

This project uses a signed 64‑bit integer to represent security roles,
user feature flags and RPC capabilities. Bit 63 is unused to avoid the
sign bit. The high bits define system roles and the low bits are used
for user level flags.

## Role Bit Assignments

| Bit | Hex Value             | Role Name          | Notes |
|----:|----------------------:|-------------------|------|
| 62  | `0x4000000000000000`  | `ROLE_SERVICE_ADMIN` | Access to service configuration and secrets |
| 61  | `0x2000000000000000`  | `ROLE_SYSTEM_ADMIN`  | Access to system administration features |
| 60  | `0x1000000000000000`  | *(reserved)*        | |
| 59  | `0x0800000000000000`  | `ROLE_MODERATOR`     | Access to moderation tools |
| 58  | `0x0400000000000000`  | `ROLE_SUPPORT`       | Access to support utilities |
| 57  | `0x0200000000000000`  | *(reserved)*        | |
| 56  | `0x0100000000000000`  | *(reserved)*        | |
| ... | ...                   |                    | |
| 0   | `0x0000000000000001`  | `ROLE_REGISTERED`    | Assigned automatically to authenticated users |

`ROLE_GLOBAL_ADMIN = ROLE_SERVICE_ADMIN | ROLE_SYSTEM_ADMIN | ROLE_MODERATOR | ROLE_SUPPORT`
`ROLE_SERVICE_AGENT = ROLE_MODERATOR | ROLE_SUPPORT`

## User Enablement Flags

Bits 1–4 are used for per‑user feature flags:

| Bit | Hex Value | Flag Name            | Description |
|----:|----------:|---------------------|-------------|
| 1   | `0x0000000000000001` | `USER_LOGGED_IN`     | User has authenticated; unlocks non‑public routes |
| 2   | `0x0000000000000002` | `USER_API_ALLOWED`   | Allow REST API access |
| 3   | `0x0000000000000004` | `USER_DISCORD_ALLOWED` | Allow Discord bot access |
| 4   | `0x0000000000000008` | `USER_SOCIAL_ALLOWED`  | Allow social posting |

## Capability Masks

RPC capability masks use the lower 32‑bits for response formats and the
upper 32‑bits for callable sources.

Callable sources (bits 33–35):
- `0x0000000100000000` – `CAP_CALL_WEB`
- `0x0000000200000000` – `CAP_CALL_DISCORD`
- `0x0000000400000000` – `CAP_CALL_API`

Response formats (bits 1–4):
- `0x0000000000000001` – `CAP_RESP_TYPED`
- `0x0000000000000002` – `CAP_RESP_DISCORD`
- `0x0000000000000004` – `CAP_RESP_API`
- `0x0000000000000008` – `CAP_RESP_BSKY`

Example:
`CAPABILITY_VERSION_REPORTING = CAP_CALL_WEB | CAP_CALL_DISCORD | CAP_RESP_TYPED | CAP_RESP_DISCORD | CAP_RESP_BSKY`

At runtime each RPC is filtered by:
1. **Security Role Mask** – determines namespace access.
2. **User Capability Mask** – controls interface permissions per user.
3. **RPC Capability Mask** – where the RPC can be called from and how it may respond.
