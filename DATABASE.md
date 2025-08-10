# Database Namespace Overview

This document describes each internal database operation and groups them by domain. The list mirrors the provider registries under `server/modules/providers` and allows modules and RPC handlers to locate the relevant SQL action.

## Naming Scheme

Every database call uses a key in the form `db:{domain}:{subsystem}:{function}:{version}`. These keys are mapped to provider-specific implementations (MSSQL, future providers) that normalize the result into a common `DBResult` structure.

## Users Domain

### `providers`

| Operation | Description |
| --- | --- |
| `db:users:providers:get_by_provider_identifier:1` | Retrieve user details by provider name and external identifier. |
| `db:users:providers:create_from_provider:1` | Insert a new user using provider‑sourced credentials and defaults. |

### `profile`

| Operation | Description |
| --- | --- |
| `db:users:profile:get_profile:1` | Get extended profile information, credits and linked providers. |
| `db:users:profile:get_roles:1` | Read the role bitmask assigned to a user. |
| `db:users:profile:set_roles:1` | Update or insert the role bitmask for a user. |
| `db:users:profile:set_profile_image:1` | Set or update a user's profile image in base64 format. |

### `session`

| Operation | Description |
| --- | --- |
| `db:users:session:set_rotkey:1` | Persist a new rotation key and timestamps for token management. |
| `db:users:session:get_rotkey:1` | Retrieve the current rotation key and timestamps. |

## Public Domain

### `links`

| Operation | Description |
| --- | --- |
| `db:public:links:get_navbar_routes:1` | List navigation routes filtered by the caller's role mask. |

## Auth Domain

### `session`

| Operation | Description |
| --- | --- |
| `db:auth:session:create_session:1` | Create a session record and associated device entry for a login. |
| `db:auth:session:get_by_access_token:1` | Look up session and device data by an access token. |

## System Domain

### `config`

| Operation | Description |
| --- | --- |
| `db:system:config:get_config:1` | Read a configuration value by key. |
| `db:system:config:upsert_config:1` | Insert or update a configuration key/value pair. |
| `db:system:config:get_configs:1` | List all configuration key/value pairs. |
| `db:system:config:delete_config:1` | Delete a configuration entry. |

## Future Onboarding Workflows

The `users.providers` and `auth.session` namespaces support multi‑provider onboarding and session management. These operations will be expanded to facilitate initial system setup and automated onboarding flows for additional identity providers.
