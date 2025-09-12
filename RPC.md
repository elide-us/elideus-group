# RPC Namespace Overview

This document describes each RPC operation in the project and groups them by domain.

## Naming Scheme

Every RPC uses a URN in the form `urn:{domain}:{subsystem}:{function}:{version}`.

## Security Alignment

Each RPC domain has an aligned security role. Other than Auth and Public, all other domains require a bearer token and a security lookup before the function is executed on behalf of the user.

## Support Domain

All Support domain calls require `ROLE_SUPPORT`.

### `roles`

| Operation                           | Description                       |
| ----------------------------------- | --------------------------------- |
| `urn:support:roles:add_member:1`      | Add members to a given role.      |
| `urn:support:roles:get_members:1`     | Get members of a given role.      |
| `urn:support:roles:remove_member:1`   | Remove members from a given role. |

### `users`

| Operation                            | Description                                      |
| ------------------------------------ | ------------------------------------------------ |
| `urn:support:users:get_displayname:1`  | Get a user's display name.                       |
| `urn:support:users:get_credits:1`      | Get a user's credit amount.                      |
| `urn:support:users:set_credits:1`      | Moderator can set user credit amount.            |
| `urn:support:users:reset_display:1`    | Moderator reset of user display name to default. |

## Users Domain

All Users domain calls require `ROLE_REGISTERED`.

### `profile`

| Operation                         | Description                                    |
| --------------------------------- | ---------------------------------------------- |
| `urn:users:profile:get_profile:1` | Get a user's profile data.                     |
| `urn:users:profile:set_display:1` | A user can set their display name.             |
| `urn:users:profile:set_optin:1`   | A user can select if their email is displayed. |

### `providers`

| Operation                               | Description                                            |
| --------------------------------------- | ------------------------------------------------------ |
| `urn:users:providers:set_provider:1`    | A user can select any active provider for their email. |
| `urn:users:providers:link_provider:1`   | A user can link additional providers.                  |
| `urn:users:providers:unlink_provider:1` | A user can unlink providers.                           |

## Auth Domain

Authentication and session management calls.

### `microsoft`

| Operation                          | Description                                                                                                              |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `urn:auth:microsoft:oauth_login:1` | Validate Microsoft tokens, create a user record if necessary, and start a user session. Returns bearer and profile data. |
| `urn:auth:microsoft:oauth_relink:1` | Reactivate or relink an existing Microsoft account and refresh user data. |

### `google`

| Operation                       | Description                                                                  |
| ------------------------------ | ---------------------------------------------------------------------------- |
| `urn:auth:google:oauth_login:1` | Exchange a Google OAuth authorization code for tokens, validate them, create a user record if necessary, and start a user session. Returns bearer and profile data. |
| `urn:auth:google:oauth_relink:1` | Reactivate or relink an existing Google account and refresh user data. |

### `discord`

| Operation                       | Description                                               |
| ------------------------------ | --------------------------------------------------------- |
| `urn:auth:discord:oauth_login:1` | Placeholder endpoint for future Discord OAuth login flow. |
| `urn:auth:discord:oauth_relink:1` | Placeholder for relinking Discord accounts.               |

### `providers`

| Operation                           | Description                                                       |
| ----------------------------------- | ----------------------------------------------------------------- |
| `urn:auth:providers:unlink_last_provider:1`   | Unlink the final auth provider for a user and revoke all tokens. |

### `session`

| Operation                             | Description                                            |
| ------------------------------------- | ------------------------------------------------------ |
| `urn:auth:session:get_token:1`        | Get a bearer token for a new device session.           |
| `urn:auth:session:refresh_token:1`    | Get a new bearer token for an existing device session. |
| `urn:auth:session:invalidate_token:1` | Invalidate an existing device session token.           |
| `urn:auth:session:logout_device:1`    | Revoke the current device's session token.             |
| `urn:auth:session:get_session:1`      | Map a bearer token to its session and device details.  |

## Public (React/Frontend) Domain

User focused calls used by the React application.

### `links`

| Operation                              | Description                                                                      |
| -------------------------------------- | -------------------------------------------------------------------------------- |
| `urn:public:links:get_home_links:1`    | Returns a list of external links for the home page.                              |
| `urn:public:links:get_navbar_routes:1` | Returns route definitions for the navigation bar filtered by the caller's roles. |

### `vars`

| Operation                              | Description                                            |
| -------------------------------------- | ------------------------------------------------------ |
| `urn:public:vars:get_version:1`        | Read the configured application version.               |
| `urn:public:vars:get_hostname:1`       | Read the configured hostname.                          |
| `urn:public:vars:get_repo:1`           | Read the GitHub repository URL.                        |
| `urn:public:vars:get_ffmpeg_version:1` | Return the installed FFmpeg version.                   |
| `urn:public:vars:get_odbc_version:1`   | Return the installed Linux MSSQL ODBC driver versions. |

### `users`

| Operation                                  | Description                                      |
| ------------------------------------------- | ------------------------------------------------ |
| `urn:public:users:get_profile:1`            | Retrieve a user's public profile.                |
| `urn:public:users:get_published_files:1`    | List files a user has published to the gallery including content type.  |

## Storage Domain

Calls for user storage management. All Storage domain calls require `ROLE_STORAGE`.

### `files`

| Operation                          | Description                                                     |
| ---------------------------------- | --------------------------------------------------------------- |
| `urn:storage:files:get_files:1`    | Provide a list of files for the user.                           |
| `urn:storage:files:get_link:1`     | Get a direct link to a file.                                   |
| `urn:storage:files:get_folder_files:1` | Provide a list of files within a folder for the user.     |
| `urn:storage:files:set_gallery:1`  | Flag a file for public inclusion in the gallery.                |
| `urn:storage:files:upload_files:1` | Upload a file or files from the user into the moderation queue. |
| `urn:storage:files:delete_files:1` | Delete a file or files specified by the user.                   |
| `urn:storage:files:create_folder:1` | Create a folder at the specified path.                         |
| `urn:storage:files:delete_folder:1` | Delete a folder at the specified path.                        |
| `urn:storage:files:create_user_folder:1` | Create a root folder for the user.                       |
| `urn:storage:files:move_file:1`    | Move a file to a new location within the user's storage.       |
| `urn:storage:files:rename_file:1`  | Rename a file within the user's storage.                        |
| `urn:storage:files:get_public_files:1` | List files flagged as public.                             |
| `urn:storage:files:get_moderation_files:1` | List files flagged for moderation review.             |
| `urn:storage:files:get_metadata:1` | Get detailed metadata about a file.                            |
| `urn:storage:files:get_usage:1`    | Summarize storage utilization by type and total size.          |

## System Domain

These calls expose system administration functionality. All System domain calls require `ROLE_SYSTEM_ADMIN`.

### `config`

| Operation                           | Description                             |
| ----------------------------------- | --------------------------------------- |
| `urn:system:config:get_configs:1`   | List configuration entries.             |
| `urn:system:config:upsert_config:1` | Create or update a configuration entry. |
| `urn:system:config:delete_config:1` | Delete a configuration entry.           |

### `roles`

| Operation                          | Description                          |
| ---------------------------------- | ------------------------------------ |
| `urn:system:roles:get_roles:1`   | List system roles.                   |
| `urn:system:roles:upsert_role:1` | Create or update a system role.      |
| `urn:system:roles:delete_role:1` | Delete a system role.                |

### `storage`

| Operation                           | Description                                        |
| ----------------------------------- | -------------------------------------------------- |
| `urn:system:storage:get_stats:1`    | Return counts and sizes for storage and cache.     |

## Service Domain

All Service domain calls require `ROLE_SERVICE_ADMIN`. Role management
operations require `ROLE_ACCOUNT_ADMIN`. `urn:service:roles:get_roles:1`
may also be called by users with `ROLE_SYSTEM_ADMIN`.

### `general`

| Operation                         | Description                         |
| --------------------------------- | ----------------------------------- |
| `urn:service:health_check:1`     | Placeholder service health check.  |

### `roles`

| Operation                               | Description                                  |
| --------------------------------------- | -------------------------------------------- |
| `urn:service:roles:get_roles:1`   | List all role names and their bit positions. |
| `urn:service:roles:upsert_role:1` | Create or update a role definition.          |
| `urn:service:roles:delete_role:1` | Delete a role.                               |

### `routes`

| Operation                          | Description                          |
| ---------------------------------- | ------------------------------------ |
| `urn:service:routes:get_routes:1`   | List application routes.             |
| `urn:service:routes:upsert_route:1` | Create or update a route definition. |
| `urn:service:routes:delete_route:1` | Delete a route definition.           |

## Account Domain

All Account domain calls require `ROLE_ACCOUNT_ADMIN`.

### `role`

| Operation                                   | Description                                  |
| ------------------------------------------- | -------------------------------------------- |
| `urn:account:role:get_roles:1`              | List all role names and their bit positions. |
| `urn:account:role:get_role_members:1`       | Get members and non-members for a role.      |
| `urn:account:role:add_role_member:1`        | Add members to a role.                       |
| `urn:account:role:remove_role_member:1`     | Remove members from a role.                  |

### `user`

| Operation                                | Description                               |
| ---------------------------------------- | ----------------------------------------- |
| `urn:account:user:get_displayname:1`     | Get a user's display name.                |
| `urn:account:user:get_credits:1`         | Get a user's credit amount.               |
| `urn:account:user:set_credits:1`         | Set a user's credit amount.               |
| `urn:account:user:reset_display:1`       | Reset a user's display name to default.   |
| `urn:account:user:create_folder:1`       | Create a folder for the user in storage.  |

## Moderation Domain

All Moderation domain calls require `ROLE_MODERATOR`.

### `content`

| Operation                            | Description                          |
| ------------------------------------ | ------------------------------------ |
| `urn:moderation:content:review_content:1` | Placeholder content review task.    |

## Discord Domain

All Discord domain calls require `ROLE_DISCORD_BOT`.

Currently exposes placeholder Discord command operations.

### `command`

| Operation                                | Description                      |
| ---------------------------------------- | -------------------------------- |
| `urn:discord:command:text_uwu:1`         | Stub command returning "uwu" text. |

