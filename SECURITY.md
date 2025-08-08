# Security Roles and Capability Masks

This project uses a signed 64‑bit integer to represent security roles,
user feature flags and RPC capabilities. Bit 63 is unused to avoid the
sign bit. The high bits define system roles and the low bits are used
for user level flags.

## Role Bit Assignments

| Bit | Hex Value             | Role Name                 | Notes |
|----:|----------------------:|---------------------------|------|
| 62  | `0x4000000000000000`  | `ROLE_SERVICE_ADMIN`      | The configuration of the service, such as API keys |
| 61  | `0x2000000000000000`  | `ROLE_SYSTEM_ADMIN`       | Access to system configuration features |
| 60  | `0x1000000000000000`  | `ROLE_SECURITY_ADMIN`     | Manage security role definitions and user assignments |
| 59  | `0x0800000000000000`  | `ROLE_MODERATION_SUPPORT` | Access to moderation tools |
| 58  | `0x0400000000000000`  | `ROLE_ADMIN_SUPPORT`      | Access to support utilities |
| 57  | `0x0200000000000000`  | *(reserved)*              | |
| 56  | `0x0100000000000000`  | *(reserved)*              | |
| ... | ...                   |                           | |
| 4   | `0x0000000000000010`  | `ROLE_API_ENABLED`        | Allows the user to post content to social media sites |
| 3   | `0x0000000000000008`  | `ROLE_SOCIAL_ENABLED`     | Allows the user to create tokens to interact with the system via API |
| 2   | `0x0000000000000004`  | `ROLE_DISCORD_ENABLED`    | Allows the user to interact with the system via Discord |
| 1   | `0x0000000000000002`  | `ROLE_STORAGE_ENABLED`    | Allows access to the storage domain |
| 0   | `0x0000000000000001`  | `ROLE_USERS_ENABLED`      | Grants access to profile and provider management |

## Role Macros

`ROLE_GLOBAL_ADMIN = ROLE_SERVICE_ADMIN | ROLE_SYSTEM_ADMIN | ROLE_MODERATION_SUPPORT | ROLE_ADMIN_SUPPORT`
`ROLE_SERVICE_AGENT = ROLE_MODERATION_SUPPORT | ROLE_ADMIN_SUPPORT`

`ROLE_USER_UNRESTRICTED = ROLE_USERS_ENABLED | ROLE_STORAGE_ENABLED | ROLE_DISCORD_ENABLED | ROLE_SOCIAL_ENABLED | ROLE_API_ENABLED`
`ROLE_USER_RESTRICTED = ROLE_USERS_ENABLED | ROLE_STORAGE_ENABLED`
`ROLE_USER_ABSTRACT = ROLE_USERS_ENABLED | ROLE_STORAGE_ENABLED | ROLE_API_ENABLED`
`ROLE_USER_INTERACTIVE = ROLE_USERS_ENABLED | ROLE_STORAGE_ENABLED | ROLE_DISCORD_ENABLED | ROLE_SOCIAL_ENABLED`

## Capability Masks

RPC capability masks use the lower 32‑bits for response formats and the
upper 32‑bits for callable sources. This is meant to provide a filtering 
mechanism to ensure responses are able to be formatted for the task channel

Callable sources (bits 33–35):
- `0x0000000100000000` – `CAP_CALL_WEB`
- `0x0000000200000000` – `CAP_CALL_DISCORD`
- `0x0000000400000000` – `CAP_CALL_API`

Response formats (bits 1–4):
- `0x0000000000000001` – `CAP_RESP_TYPED`
- `0x0000000000000002` – `CAP_RESP_DISCORD`
- `0x0000000000000004` – `CAP_RESP_API`
- `0x0000000000000008` – `CAP_RESP_BSKY`
