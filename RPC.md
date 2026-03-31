# RPC Namespace Overview

This document describes each RPC operation in the project and groups them by domain.

## Naming Scheme

Every RPC uses a URN in the form `urn:{domain}:{subsystem}:{function}:{version}`.

## Security Alignment

Each RPC domain has an aligned security role. Other than Auth and Public, all other domains require a bearer token and a security lookup before the function is executed on behalf of the user.

## Frontend Binding Generators

- `python scripts/generate_rpc_bindings.py` regenerates RPC models and `frontend/src/rpc/**/index.ts` accessors.
- `python scripts/generate_db_namespace.py` regenerates Query Registry models plus DB helper functions in `frontend/src/db/namespace.ts`.

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

### `pages`

| Operation | Description |
| --- | --- |
| `urn:users:pages:create_version:1` | Create a new page version for an editable page identified by slug. |
| `urn:users:pages:list_versions:1` | List version history for an editable page identified by slug. |
| `urn:users:pages:get_version:1` | Fetch a specific page version for an editable page identified by slug. |

### `products`

| Operation | Description |
| --- | --- |
| `urn:users:products:list:1` | List active purchasable products with per-user enablement state. |
| `urn:users:products:purchase:1` | Purchase a product using the stub payment flow. |

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
| `urn:auth:discord:oauth_login:1` | Exchange Discord authorization code for tokens and create a session. |
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

| Operation                              | Description |
| -------------------------------------- | ----------- |
| `urn:public:vars:get_versions:1`       | Return public metadata (version, hostname, repo) and, when authorized with `ROLE_SERVICE_ADMIN`, include FFmpeg and ODBC component versions. |

### `users`

| Operation                                  | Description                                      |
| ------------------------------------------- | ------------------------------------------------ |
| `urn:public:users:get_profile:1`            | Retrieve a user's public profile.                |
| `urn:public:users:get_published_files:1`    | List files a user has published to the gallery including content type.  |

### `pages`

| Operation | Description |
| --- | --- |
| `urn:public:pages:list_pages:1` | List active published pages, optionally filtered by page_type. |
| `urn:public:pages:get_page:1` | Get a page by slug including latest version content. Returns 404 if not found or inactive. |

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


### `conversations`

| Operation | Description |
| --- | --- |
| `urn:system:conversations:list_conversations:1` | List conversation rows with pagination metadata. |
| `urn:system:conversations:get_stats:1` | Return aggregate conversation/thread/token statistics. |
| `urn:system:conversations:view_thread:1` | Return the full message history for a thread id. |
| `urn:system:conversations:delete_thread:1` | Delete all conversation rows for a thread id. |
| `urn:system:conversations:delete_before:1` | Delete conversation rows created before a timestamp. |

### `models`

| Operation | Description |
| --- | --- |
| `urn:system:models:get_models:1` | List registered models and available API providers. |
| `urn:system:models:upsert_model:1` | Create or update a model registry row. |
| `urn:system:models:delete_model:1` | Delete a model registry row by recid or name. |

### `scheduled_tasks`

| Operation | Description |
| --- | --- |
| `urn:system:scheduled_tasks:list:1` | List scheduled task definitions. |
| `urn:system:scheduled_tasks:get:1` | Get a scheduled task definition by recid. |
| `urn:system:scheduled_tasks:list_history:1` | List execution history rows for a scheduled task. |
| `urn:system:scheduled_tasks:run_now:1` | Trigger an immediate workflow run for a scheduled task. |

### `workflows`

| Operation | Description |
| --- | --- |
| `urn:system:workflows:list_workflows:1` | List workflow definitions, optionally filtered by status. |
| `urn:system:workflows:get_workflow:1` | Get one workflow and its configured action sequence. |
| `urn:system:workflows:list_runs:1` | List workflow runs, optionally filtered by status. |
| `urn:system:workflows:get_run:1` | Get one workflow run by guid. |
| `urn:system:workflows:submit_run:1` | Submit a new workflow run for a workflow name. |
| `urn:system:workflows:cancel_run:1` | Cancel an in-flight workflow run. |
| `urn:system:workflows:rollback_run:1` | Roll back a workflow run. |
| `urn:system:workflows:resume_run:1` | Resume a paused or waiting workflow run. |
| `urn:system:workflows:retry_run_action:1` | Retry a failed workflow run action. |
| `urn:system:workflows:list_run_actions:1` | List action rows for a workflow run. |
| `urn:system:workflows:scan_stalls:1` | Scan workflows for stalled runs/actions and return findings. |

## Service Domain

All Service domain calls require `ROLE_SERVICE_ADMIN`. Role management
operations require `ROLE_ACCOUNT_ADMIN`. `urn:service:roles:get_roles:1`
may also be called by users with `ROLE_SYSTEM_ADMIN`.

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


### `pages`

| Operation | Description |
| --- | --- |
| `urn:service:pages:list:1` | List all content pages (including inactive) for administration. |
| `urn:service:pages:create:1` | Create a content page with initial content/version. |
| `urn:service:pages:update:1` | Update page metadata fields by `recid`. |
| `urn:service:pages:delete:1` | Soft-delete a page by `recid`. |

### `renewals`

| Operation | Description |
| --- | --- |
| `urn:service:renewals:list:1` | List renewal records with optional category and status filters. |
| `urn:service:renewals:get:1` | Get a renewal record by `recid`. |
| `urn:service:renewals:upsert:1` | Create or update a renewal record. |
| `urn:service:renewals:delete:1` | Delete a renewal record by `recid`. |

### `payment_requests`

| Operation | Description |
| --- | --- |
| `urn:service:payment_requests:create:1` | Create an accounts payable staging payment request in Pending Approval status for manager review. |

### `reflection`

| Operation | Description |
| --- | --- |
| `urn:service:reflection:list_tables:1` | List tables from the reflection schema catalog. |
| `urn:service:reflection:describe_table:1` | Return columns, indexes, and foreign keys for a table. |
| `urn:service:reflection:list_views:1` | List database views with definitions. |
| `urn:service:reflection:get_full_schema:1` | Return the complete reflection schema snapshot. |
| `urn:service:reflection:get_schema_version:1` | Return the current schema version. |
| `urn:service:reflection:dump_table:1` | Export table rows as JSON with a configurable row limit. |
| `urn:service:reflection:query_info_schema:1` | Query whitelisted INFORMATION_SCHEMA views. |
| `urn:service:reflection:list_domains:1` | Enumerate QueryRegistry domains, subdomains, and operations. |
| `urn:service:reflection:list_rpc_endpoints:1` | List available top-level RPC domain handler names. |

### `rpcdispatch`

| Operation | Description |
| --- | --- |
| `urn:service:rpcdispatch:list_domains:1` | List domain rows from `reflection_rpc_domains`. |
| `urn:service:rpcdispatch:list_subdomains:1` | List subdomain rows from `reflection_rpc_subdomains`. |
| `urn:service:rpcdispatch:list_functions:1` | List function rows from `reflection_rpc_functions`. |
| `urn:service:rpcdispatch:list_models:1` | List model rows from `reflection_rpc_models`. |
| `urn:service:rpcdispatch:list_model_fields:1` | List model field rows from `reflection_rpc_model_fields`. |

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

All Discord domain calls require the role mapped to the `discord` RPC domain in `system_roles.element_rpc_domain` (currently `ROLE_DISCORD_ADMIN`). Requests must include the `x-discord-id` (or `x-discord-user-id`) header identifying the caller. If headers cannot be set, provide the identifier as `discord_id` within the request payload.

Currently exposes Discord command, chat, persona, and Bluesky bridge operations.

### `bsky`

| Operation                             | Description                                   |
| ------------------------------------- | --------------------------------------------- |
| `urn:discord:bsky:post:1`             | Post a message to the configured Bluesky feed. |

### `command`

| Operation                                | Description                      |
| ---------------------------------------- | -------------------------------- |
| `urn:discord:command:get_roles:1`        | List security roles for a Discord user. |


### `chat`

| Operation                                   | Description                     |
| ------------------------------------------- | ------------------------------- |
| `urn:discord:chat:summarize_channel:1`      | Summarize a Discord channel.    |
| `urn:discord:chat:persona_response:1`       | Respond using a selected persona. |

### `personas`

| Operation                                   | Description                                   |
| ------------------------------------------- | --------------------------------------------- |
| `urn:discord:personas:get_personas:1`       | List Discord assistant personas.              |
| `urn:discord:personas:get_models:1`         | List available assistant models.              |
| `urn:discord:personas:upsert_persona:1`     | Create or update a Discord assistant persona. |
| `urn:discord:personas:delete_persona:1`     | Delete a Discord assistant persona.           |

#### Usage Examples

```text
!summarize 24
```
Summarize the last 24 hours of messages in the current channel and send the result as a DM.

## Finance Domain

Finance domain calls generally require `ROLE_FINANCE_ADMIN`.
`urn:finance:staging:promote:1`, all `pipeline_config` operations, all `staging_account_map` operations, all `staging_purge_log` operations, and all `vendors` operations require `ROLE_SYSTEM_ADMIN`.

### `accounts`

| Operation | Description |
| --- | --- |
| `urn:finance:accounts:list:1` | List chart-of-accounts rows. |
| `urn:finance:accounts:get:1` | Get an account by GUID. |
| `urn:finance:accounts:upsert:1` | Create or update a chart-of-accounts row. |
| `urn:finance:accounts:delete:1` | Delete an account by GUID. |
| `urn:finance:accounts:list_children:1` | List child accounts for a parent account GUID. |

### `credit_lots`

| Operation | Description |
| --- | --- |
| `urn:finance:credit_lots:list_by_user:1` | List credit lots owned by a user GUID. |
| `urn:finance:credit_lots:get:1` | Get one credit lot by recid. |
| `urn:finance:credit_lots:create:1` | Create a credit lot allocation for a user. |
| `urn:finance:credit_lots:consume:1` | Consume credits from available lots with ledgered consumption details. |
| `urn:finance:credit_lots:expire:1` | Expire a credit lot and update remaining balance. |
| `urn:finance:credit_lots:list_events:1` | List lifecycle events for a credit lot. |
| `urn:finance:credit_lots:wallet_balance:1` | Return wallet balance summary for a user GUID. |

### `dimensions`

| Operation | Description |
| --- | --- |
| `urn:finance:dimensions:list:1` | List finance dimensions. |
| `urn:finance:dimensions:list_by_name:1` | List dimension rows filtered by dimension name. |
| `urn:finance:dimensions:get:1` | Get a finance dimension by recid. |
| `urn:finance:dimensions:upsert:1` | Create or update a finance dimension row. |
| `urn:finance:dimensions:delete:1` | Delete a finance dimension by recid. |

### `journals`

| Operation | Description |
| --- | --- |
| `urn:finance:journals:list:1` | List journals with optional status/period filters. |
| `urn:finance:journals:get:1` | Get a single journal by record id. |
| `urn:finance:journals:get_lines:1` | List lines for a journal record id. |
| `urn:finance:journals:create:1` | Create a draft journal with lines. |
| `urn:finance:journals:submit_for_approval:1` | Submit a draft journal for manager approval. |
| `urn:finance:journals:approve:1` | Approve a pending journal and post it to the GL. |
| `urn:finance:journals:reject:1` | Reject a pending journal back to Draft status. |
| `urn:finance:journals:reverse:1` | Reverse a posted journal. |

### `ledgers`

| Operation | Description |
| --- | --- |
| `urn:finance:ledgers:list:1` | List all ledgers with fiscal year, status, and timestamps. |
| `urn:finance:ledgers:get:1` | Get a single ledger by record id. |
| `urn:finance:ledgers:create:1` | Create a ledger with optional fiscal year and chart-of-accounts association. |
| `urn:finance:ledgers:update:1` | Update ledger metadata and active status. |
| `urn:finance:ledgers:delete:1` | Soft-delete a ledger when no journals reference it. |

### `numbers`

| Operation | Description |
| --- | --- |
| `urn:finance:numbers:list:1` | List number sequences. |
| `urn:finance:numbers:get:1` | Get one number sequence by record id. |
| `urn:finance:numbers:upsert:1` | Create or update a number sequence. |
| `urn:finance:numbers:delete:1` | Delete a number sequence by record id. |
| `urn:finance:numbers:next_number:1` | Consume the next allocated number block from a sequence. |
| `urn:finance:numbers:shift:1` | Close an active sequence and create a new active sequence for the same account. |

### `pipeline_config`

| Operation | Description |
| --- | --- |
| `urn:finance:pipeline_config:list:1` | List finance pipeline configuration entries, optionally filtered by pipeline name. |
| `urn:finance:pipeline_config:get:1` | Get a single finance pipeline configuration entry by pipeline and key. |
| `urn:finance:pipeline_config:upsert:1` | Create or update a finance pipeline configuration entry. |
| `urn:finance:pipeline_config:delete:1` | Delete a finance pipeline configuration entry by record id. |

### `periods`

| Operation | Description |
| --- | --- |
| `urn:finance:periods:list:1` | List fiscal periods across all fiscal years. |
| `urn:finance:periods:list_by_year:1` | List periods for one fiscal year. |
| `urn:finance:periods:get:1` | Get a single fiscal period by GUID. |
| `urn:finance:periods:close:1` | Close an open fiscal period after all blocking items are resolved. |
| `urn:finance:periods:reopen:1` | Reopen a closed fiscal period. |
| `urn:finance:periods:lock:1` | Lock a closed fiscal period. |
| `urn:finance:periods:unlock:1` | Unlock a locked fiscal period back to closed status. |
| `urn:finance:periods:list_close_blockers:1` | List blocking journals, imports, and revenue recognition items for period close review. |
| `urn:finance:periods:upsert:1` | Create or update fiscal period metadata. |
| `urn:finance:periods:delete:1` | Delete a fiscal period by GUID. |
| `urn:finance:periods:generate_calendar:1` | Generate the 4-4-5 fiscal calendar for a year, rejecting duplicate generation. |

### `products`

| Operation | Description |
| --- | --- |
| `urn:finance:products:list:1` | List finance products. |
| `urn:finance:products:get:1` | Get a finance product by `recid` or `sku`. |
| `urn:finance:products:upsert:1` | Create or update a finance product. |
| `urn:finance:products:delete:1` | Delete a finance product by `recid`. |

### `product_journal_config`

| Operation | Description |
| --- | --- |
| `urn:finance:product_journal_config:list:1` | List product journal configuration rows. |
| `urn:finance:product_journal_config:get:1` | Get a product journal configuration row by `recid`. |
| `urn:finance:product_journal_config:upsert:1` | Create or update a product journal configuration row. |
| `urn:finance:product_journal_config:approve:1` | Approve a draft product journal configuration. |
| `urn:finance:product_journal_config:activate:1` | Activate an approved product journal configuration. |
| `urn:finance:product_journal_config:close:1` | Close an active product journal configuration. |

### `reporting`

| Operation | Description |
| --- | --- |
| `urn:finance:reporting:trial_balance:1` | List trial balance rows by fiscal year or period. |
| `urn:finance:reporting:journal_summary:1` | List journal totals and status by period. |
| `urn:finance:reporting:period_status:1` | List period close status metrics for the fiscal calendar. |
| `urn:finance:reporting:credit_lot_summary:1` | List credit lot balance and usage summaries. |

### `staging`

| Operation | Description |
| --- | --- |
| `urn:finance:staging:delete_import:1` | Delete a finance staging import batch and its staged child rows. |
| `urn:finance:staging:import:1` | Trigger an Azure billing cost-details import for a date range; successful imports now land in Pending Approval status. |
| `urn:finance:staging:import_invoices:1` | Trigger an Azure invoice import for a billing month (`YYYY-MM`); successful imports now land in Pending Approval status. |
| `urn:finance:staging:list_imports:1` | List finance staging import batches, optionally filtered by `status`. |
| `urn:finance:staging:list_details:1` | List imported cost detail rows for a staging import batch. |
| `urn:finance:staging:list_line_items:1` | List generalized staging line items for a staging import batch. |
| `urn:finance:staging:approve:1` | Approve a Pending Approval staging import to Approved status; requires `ROLE_FINANCE_APPR`. |
| `urn:finance:staging:reject:1` | Reject a Pending Approval staging import and record an optional reason; requires `ROLE_FINANCE_APPR`. |
| `urn:finance:staging:promote:1` | Submit async promotion of an Approved staging import into a posted journal and return task guid. |

### `staging_account_map`

| Operation | Description |
| --- | --- |
| `urn:finance:staging_account_map:list:1` | List billing service-to-account mapping rules with account metadata. |
| `urn:finance:staging_account_map:upsert:1` | Create or update a billing service-to-account mapping rule. |
| `urn:finance:staging_account_map:delete:1` | Delete a billing service-to-account mapping rule. |

### `staging_purge_log`

| Operation | Description |
| --- | --- |
| `urn:finance:staging_purge_log:list:1` | List purge log records used to track staged import purges by vendor and period. |

### `vendors`

| Operation | Description |
| --- | --- |
| `urn:finance:vendors:list:1` | List finance vendors used by billing imports and payment requests. |
| `urn:finance:vendors:upsert:1` | Create or update a finance vendor. |
| `urn:finance:vendors:delete:1` | Delete a finance vendor by record id. |
