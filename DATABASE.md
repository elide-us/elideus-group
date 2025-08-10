# Database Namespace Overview

This document describes each internal database operation and groups them by domain. The namespace mirrors RPCs and is organized by domain and subsystem to support module and frontend integration.

## Naming Scheme

Every database operation uses a URN in the form `db:{domain}:{subsystem}:{function}:{version}`. Providers register handlers for these operations and the database module dispatches calls through the selected provider.

## Providers

`DatabaseModule` selects a provider at startup and exposes a `run` method that delegates to provider-specific registries. Configuration comes from environment variables such as `DATABASE_PROVIDER` and DSN strings.

## Users Domain

Operations supporting user accounts and onboarding.

### `providers`

| Operation | Description |
| --- | --- |
| `db:users:providers:get_by_provider_identifier:1` | Fetch a user record using an external provider and identifier. |
| `db:users:providers:create_from_provider:1` | Insert a new user based on provider data, returning the created record. |

### `profile`

| Operation | Description |
| --- | --- |
| `db:users:profile:get_profile:1` | Retrieve profile details including email, credits, providers and profile image. |
| `db:users:profile:get_roles:1` | Read the stored role bitmask for a user. |
| `db:users:profile:set_roles:1` | Update or insert the role bitmask for a user. |
| `db:users:profile:set_profile_image:1` | Upsert a profile image for the user. |

### `session`

| Operation | Description |
| --- | --- |
| `db:users:session:set_rotkey:1` | Store the current rotation key and metadata for a user. |
| `db:users:session:get_rotkey:1` | Retrieve the rotation key metadata for a user. |

## Auth Domain

Session management operations used by authentication workflows.

### `session`

| Operation | Description |
| --- | --- |
| `db:auth:session:create_session:1` | Create session and device records with access token information. |
| `db:auth:session:get_by_access_token:1` | Lookup session and device details by access token. |

## Public Domain

Frontend-facing operations.

### `links`

| Operation | Description |
| --- | --- |
| `db:public:links:get_navbar_routes:1` | Return navigation routes filtered by role mask. |

## System Domain

Administrative configuration operations supporting initial system setup.

### `config`

| Operation | Description |
| --- | --- |
| `db:system:config:get_config:1` | Fetch a configuration entry by key. |
| `db:system:config:upsert_config:1` | Insert or update a configuration entry. |
| `db:system:config:get_configs:1` | List all configuration entries. |
| `db:system:config:delete_config:1` | Remove a configuration entry. |

## Future Onboarding

The `users.providers` operations enable creation and linking of accounts across multiple identity providers. Combined with system configuration calls, they form the basis for upcoming onboarding workflows for both initial setup and new user registration.

