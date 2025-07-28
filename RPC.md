# RPC Namespace Overview

This document describes each RPC operation in the project and groups them by domain. The list mirrors `rpc/metadata.json`.

## Naming Scheme

Every RPC uses a URN in the form `urn:{domain}:{subsystem}:{function}:{version}`. Handlers automatically append a `:view:default:1` suffix when no `view` is specified. Custom views may transform the payload for different clients (e.g. Discord).

## System Domain

These calls expose system administration functionality.


### `roles`

| Operation | Description |
|-----------|-------------|
| `urn:system:roles:list:1` | List all role names and their bit positions. |
| `urn:system:roles:set:1` | Create or update a role definition. |
| `urn:system:roles:delete:1` | Delete a role. |
| `urn:system:roles:get_members:1` | Get members and non-members for a role. |
| `urn:system:roles:add_member:1` | Add a user to a role. |
| `urn:system:roles:remove_member:1` | Remove a user from a role. |

### `users`

| Operation | Description |
|-----------|-------------|
| `urn:system:users:list:1` | List all users. |
| `urn:system:users:get_roles:1` | Get the roles assigned to a user. |
| `urn:system:users:set_roles:1` | Replace the roles assigned to a user. |
| `urn:system:users:list_roles:1` | List available role names. |
| `urn:system:users:list_roles:2` | List available role names. |
| `urn:system:users:get_profile:1` | Retrieve profile information for a user. |
| `urn:system:users:set_credits:1` | Update a user's credit balance. |


## Auth Domain

Authentication and session management calls.

### `microsoft`

| Operation | Description |
|-----------|-------------|
| `urn:auth:microsoft:user_login:1` | Validate Microsoft tokens, create a user record if necessary, and start a user session. Returns bearer and rotation tokens plus profile data. |

### `session`

| Operation | Description |
|-----------|-------------|
| `urn:auth:session:refresh:1` | Exchange a rotation token for new session tokens. |
| `urn:auth:session:invalidate:1` | Invalidate an existing session using its rotation token. |

## Frontend Domain

User focused calls used by the React application.

### `user`

| Operation | Description |
|-----------|-------------|
| `urn:frontend:user:get_profile_data:1` | Fetch the profile associated with a bearer token. |
| `urn:frontend:user:set_display_name:1` | Update the user's display name and return the updated profile. |

### `links`

| Operation | Description |
|-----------|-------------|
| `urn:frontend:links:get_home:1` | Returns a list of external links for the home page. |
| `urn:frontend:links:get_routes:1` | Returns route definitions for the navigation bar filtered by the caller's roles. |

### `vars`

| Operation | Description |
|-----------|-------------|
| `urn:frontend:vars:get_version:1` | Read the configured application version. |
| `urn:frontend:vars:get_hostname:1` | Read the configured hostname. |
| `urn:frontend:vars:get_repo:1` | Read the GitHub repository URL. |
| `urn:frontend:vars:get_ffmpeg_version:1` | Return the installed FFmpeg version. |

## Functional Areas

### Login System

The front-end uses Microsoft OAuth via MSAL. `LoginPage.tsx` prompts the user to authenticate and then calls `urn:auth:microsoft:user_login:1`. The response supplies bearer and rotation tokens which are stored locally and used for subsequent RPC calls. Session refresh and invalidation are handled through the `auth:session` endpoints.

### User Pages

`UserPage.tsx` displays the current user's profile and allows updating the display name. It calls `frontend:user:get_profile_data` on load and `frontend:user:set_display_name` when saving changes.

### System Pages

The React application provides several administration pages:

- `AccountUsersPage` lists users. Selecting a user opens `AccountUserPanel` where roles and credits can be modified via the `account:users` RPCs.
- `SystemRolesPage` manages role definitions using the `system:roles` endpoints.
 - `AccountRoleMembersPage` manages membership for each role through `account:roles` membership operations.

Navigation links and routes for these pages are loaded from the server using the `frontend:links` RPCs so that access can be filtered by user roles.

## Security Roles

Role bits are defined in `SECURITY.md`. Key high level roles include SERVICE ADMIN, SYSTEM ADMIN, MODERATOR and SUPPORT. These will control access to future RPC domains such as a planned `service` namespace for service-wide configuration.

