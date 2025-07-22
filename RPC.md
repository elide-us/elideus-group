# RPC Namespace Overview

This document describes each RPC operation in the project and groups them by domain. The list mirrors `rpc/metadata.json`.

## Naming Scheme

Every RPC uses a URN in the form `urn:{domain}:{subsystem}:{function}:{version}`. Handlers automatically append a `:view:default:1` suffix when no `view` is specified. Custom views may transform the payload for different clients (e.g. Discord).

## Admin Domain

These calls expose server administration functionality.

### `links`

| Operation | Description |
|-----------|-------------|
| `urn:admin:links:get_home:1` | Returns a list of external links for the home page. |
| `urn:admin:links:get_routes:1` | Returns route definitions for the navigation bar filtered by the caller's roles. |

### `roles`

| Operation | Description |
|-----------|-------------|
| `urn:admin:roles:list:1` | List all role names and their bit positions. |
| `urn:admin:roles:set:1` | Create or update a role definition. |
| `urn:admin:roles:delete:1` | Delete a role. |
| `urn:admin:roles:get_members:1` | Get members and non-members for a role. |
| `urn:admin:roles:add_member:1` | Add a user to a role. |
| `urn:admin:roles:remove_member:1` | Remove a user from a role. |

### `users`

| Operation | Description |
|-----------|-------------|
| `urn:admin:users:list:1` | List all users. |
| `urn:admin:users:get_roles:1` | Get the roles assigned to a user. |
| `urn:admin:users:set_roles:1` | Replace the roles assigned to a user. |
| `urn:admin:users:list_roles:1` | List available role names. |
| `urn:admin:users:get_profile:1` | Retrieve profile information for a user. |
| `urn:admin:users:set_credits:1` | Update a user's credit balance. |

### `vars`

| Operation | Description |
|-----------|-------------|
| `urn:admin:vars:get_version:1` | Read the configured application version. |
| `urn:admin:vars:get_hostname:1` | Read the configured hostname. |
| `urn:admin:vars:get_repo:1` | Read the GitHub repository URL. |
| `urn:admin:vars:get_ffmpeg_version:1` | Return the installed FFmpeg version. |

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

## Functional Areas

### Login System

The front-end uses Microsoft OAuth via MSAL. `LoginPage.tsx` prompts the user to authenticate and then calls `urn:auth:microsoft:user_login:1`. The response supplies bearer and rotation tokens which are stored locally and used for subsequent RPC calls. Session refresh and invalidation are handled through the `auth:session` endpoints.

### User Pages

`UserPage.tsx` displays the current user's profile and allows updating the display name. It calls `frontend:user:get_profile_data` on load and `frontend:user:set_display_name` when saving changes.

### Admin Pages

The React application provides several administration pages:

- `AdminUsersPage` lists users. Selecting a user opens `AdminUserPanel` where roles and credits can be modified via the `admin:users` RPCs.
- `AdminRolesPage` manages role definitions using the `admin:roles` endpoints.
- `AdminRoleMembersPage` manages membership for each role through `admin:roles` membership operations.

Navigation links and routes for these pages are loaded from the server using the `admin:links` RPCs so that access can be filtered by user roles.

## Security Roles

Role bits are defined in `SECURITY.md`. Key high level roles include SERVICE ADMIN, SYSTEM ADMIN, MODERATOR and SUPPORT. These will control access to future RPC domains such as a planned `service` namespace for service-wide configuration.

