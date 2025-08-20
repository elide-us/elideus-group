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
| `urn:support:users:get_profile:1`      | Get a user's profile details.                    |
| `urn:support:users:set_credits:1`      | Moderator can set user credit amount.            |
| `urn:support:users:enable_storage:1`   | Moderator can enable user storage.               |
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

### `session`

| Operation                             | Description                                            |
| ------------------------------------- | ------------------------------------------------------ |
| `urn:auth:session:get_token:1`        | Get a bearer token for a new device session.           |
| `urn:auth:session:refresh_token:1`    | Get a new bearer token for an existing device session. |
| `urn:auth:session:invalidate_token:1` | Invalidate an existing device session token.           |
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

## Storage Domain

Calls for user storage management. All Storage domain calls require `ROLE_STORAGE`.

### `files`

| Operation                          | Description                                                     |
| ---------------------------------- | --------------------------------------------------------------- |
| `urn:storage:files:get_files:1`    | Provide a list of files for the user.                           |
| `urn:storage:files:set_gallery:1`  | Flag a file for public inclusion in the gallery.                |
| `urn:storage:files:upload_files:1` | Upload a file or files from the user into the moderation queue. |
| `urn:storage:files:delete_files:1` | Delete a file or files specified by the user.                   |

## System Domain

These calls expose system administration functionality. All System domain calls require `ROLE_SYSTEM_ADMIN`.

### `config`

| Operation                           | Description                             |
| ----------------------------------- | --------------------------------------- |
| `urn:system:config:get_configs:1`   | List configuration entries.             |
| `urn:system:config:upsert_config:1` | Create or update a configuration entry. |
| `urn:system:config:delete_config:1` | Delete a configuration entry.           |

### `routes`

| Operation                          | Description                          |
| ---------------------------------- | ------------------------------------ |
| `urn:system:routes:get_routes:1`   | List application routes.             |
| `urn:system:routes:upsert_route:1` | Create or update a route definition. |
| `urn:system:routes:delete_route:1` | Delete a route definition.           |

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
| `urn:service:roles:get_roles:1`         | List all role names and their bit positions. |
| `urn:service:roles:get_role_members:1`  | Get members and non-members for a role.      |
| `urn:service:roles:add_role_member:1`   | Add members to a role.                       |
| `urn:service:roles:remove_role_member:1` | Remove members from a role.                 |
| `urn:service:roles:upsert_role:1`       | Create or update a role definition.          |
| `urn:service:roles:delete_role:1`       | Delete a role.                               |

## Moderation Domain

All Moderation domain calls require `ROLE_MODERATOR`.

### `content`

| Operation                            | Description                          |
| ------------------------------------ | ------------------------------------ |
| `urn:moderation:content:review_content:1` | Placeholder content review task.    |
