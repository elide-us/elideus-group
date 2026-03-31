# Query Registry Mapping

This document summarizes the current QueryRegistry layout under `queryregistry/`
and reflects the active dispatch maps in code.

## Functional groupings → query registry domains

### Content and publishing data → `content`

- `content.cache` *(stub CRUD dispatchers)*
- `content.indexing`
- `content.pages`
- `content.posts` *(stub CRUD dispatchers)*
- `content.wiki`

### Identity, sessions, and account linkages → `identity`

- `identity.audit` *(stub CRUD dispatchers)*
- `identity.auth`
- `identity.enablements`
- `identity.mcp_agents`
- `identity.profiles`
- `identity.roles`
- `identity.sessions`
- `identity.users`

### System administration and workflow data → `system`

- `system.config`
- `system.conversations`
- `system.personas`
- `system.public`
- `system.renewals`
- `system.roles`
- `system.scheduled_tasks`
- `system.workflows`

### Finance and accounting data → `finance`

- `finance.accounts`
- `finance.credit_lots`
- `finance.credits`
- `finance.dimensions`
- `finance.journal_lines`
- `finance.journals`
- `finance.ledgers`
- `finance.numbers`
- `finance.periods`
- `finance.pipeline_config`
- `finance.product_journal_config`
- `finance.products`
- `finance.reporting`
- `finance.staging`
- `finance.staging_account_map`
- `finance.staging_invoices`
- `finance.staging_line_items`
- `finance.staging_purge_log`
- `finance.status`
- `finance.vendors`

### Database reflection and self-description → `reflection`

- `reflection.schema`
- `reflection.data`

### RPC topology reflection tables → `rpcdispatch`

- `rpcdispatch.domains`
- `rpcdispatch.subdomains`
- `rpcdispatch.functions`
- `rpcdispatch.models`
- `rpcdispatch.model_fields`

### Discord operational metadata → `discord`

- `discord.guilds`
- `discord.channels`

## Dispatch contract (authoritative)

All QueryRegistry operations MUST follow:

```
db:<domain>:<subdomain>:<operation>:<version>
```

This is the only supported dispatch format.

## Handler entry points

- Root dispatch: `queryregistry/handler.py` → `queryregistry.handler.HANDLERS`
- Content: `queryregistry/content/handler.py`
- Identity: `queryregistry/identity/handler.py`
- System: `queryregistry/system/handler.py`
- Finance: `queryregistry/finance/handler.py`
- Reflection: `queryregistry/reflection/handler.py`
- RPC dispatch reflection: `queryregistry/rpcdispatch/handler.py`
- Discord: `queryregistry/discord/handler.py`

## Operation/version dispatch inventory

Each subdomain exposes versioned operation keys from its local `DISPATCHERS`
map.

| Domain | Subdomain | Operations (`:1`) |
| --- | --- | --- |
| `content` | `cache` | `create`, `read`, `update`, `delete`, `list` *(stub)* |
| `content` | `indexing` | `list`, `list_public`, `list_reported`, `replace_user`, `upsert`, `delete`, `delete_folder`, `set_public`, `set_reported`, `count_rows`, `set_gallery`, `get_published_files` |
| `content` | `pages` | `create`, `create_version`, `delete`, `get`, `get_by_slug`, `get_version`, `list`, `list_versions`, `update` |
| `content` | `posts` | `create`, `read`, `update`, `delete`, `list` *(stub)* |
| `content` | `wiki` | `list`, `get`, `get_by_slug`, `get_by_route_context`, `list_children`, `create`, `update`, `delete`, `create_version`, `list_versions`, `get_version` |
| `discord` | `guilds` | `upsert`, `get`, `list`, `update_credits` |
| `discord` | `channels` | `upsert`, `get`, `list_by_guild`, `bump_activity` |
| `finance` | `accounts` | `list`, `get`, `upsert`, `delete`, `list_children` |
| `finance` | `credit_lots` | `list_lots_by_user`, `get_lot`, `create_lot`, `consume_credits`, `expire_lot`, `list_events_by_lot`, `create_event`, `sum_remaining_by_user` |
| `finance` | `credits` | `get`, `set` |
| `finance` | `dimensions` | `list`, `list_by_name`, `get`, `upsert`, `delete` |
| `finance` | `journal_lines` | `list_by_journal`, `create_line`, `create_lines_batch`, `delete_by_journal` |
| `finance` | `journals` | `list`, `get`, `create`, `update_status`, `get_by_posting_key` |
| `finance` | `ledgers` | `create`, `delete`, `get`, `get_by_name`, `journal_reference_count`, `list`, `update` |
| `finance` | `numbers` | `list`, `get`, `get_by_prefix_account`, `get_by_scope`, `upsert`, `delete`, `close_sequence`, `next_number`, `next_number_by_scope` |
| `finance` | `periods` | `list`, `list_by_year`, `get`, `close`, `reopen`, `lock`, `unlock`, `list_close_blockers`, `upsert`, `delete`, `generate_calendar` |
| `finance` | `pipeline_config` | `list`, `get`, `upsert`, `delete` |
| `finance` | `product_journal_config` | `list`, `get`, `get_active`, `upsert`, `approve`, `activate`, `close` |
| `finance` | `products` | `list`, `get`, `upsert`, `delete` |
| `finance` | `reporting` | `trial_balance`, `journal_summary`, `period_status`, `credit_lot_summary` |
| `finance` | `staging` | `create_import`, `delete_import`, `update_import_status`, `approve_import`, `reject_import`, `insert_cost_detail_batch`, `list_imports`, `list_cost_details_by_import`, `aggregate_cost_by_service` |
| `finance` | `staging_account_map` | `list_account_map`, `get_account_map`, `upsert_account_map`, `delete_account_map`, `resolve_account` |
| `finance` | `staging_invoices` | `insert_invoice_batch`, `list_invoices_by_import`, `get_invoice_by_name`, `delete_invoices_by_import` |
| `finance` | `staging_line_items` | `insert_line_items_batch`, `list_line_items_by_import`, `aggregate_line_items`, `delete_line_items_by_import` |
| `finance` | `staging_purge_log` | `list_purge_logs`, `get_purge_log`, `check_purged_key`, `upsert_purge_log` |
| `finance` | `status` | `list`, `get_by_domain_code` |
| `finance` | `vendors` | `list_vendors`, `get_vendor`, `get_vendor_by_name`, `upsert_vendor`, `delete_vendor` |
| `identity` | `audit` | `create`, `read`, `update`, `delete`, `list` *(stub)* |
| `identity` | `auth` | `get_by_provider_identifier`, `get_any_by_provider_identifier`, `get_user_by_email`, `create_from_provider`, `link_provider`, `unlink_provider`, `unlink_last_provider`, `set_provider`, `relink`, `soft_delete_account` |
| `identity` | `enablements` | `get`, `upsert` |
| `identity` | `mcp_agents` | `register`, `get_by_client_id`, `get_by_recid`, `link_user`, `revoke`, `list_by_user`, `create_auth_code`, `consume_auth_code`, `create_token`, `get_token`, `revoke_token` |
| `identity` | `profiles` | `read`, `update`, `set_display`, `set_optin`, `set_profile_image`, `update_if_unedited`, `get_public_profile` |
| `identity` | `roles` | `list`, `list_all`, `list_non_members`, `create`, `delete`, `get_roles`, `set_roles` |
| `identity` | `sessions` | `read`, `get_rotkey`, `create_session`, `update_session`, `update_device_token`, `revoke_device_token`, `revoke_all_device_tokens`, `revoke_provider_tokens`, `set_rotkey`, `list_snapshots` |
| `identity` | `users` | `read`, `exists`, `read_by_discord` |
| `reflection` | `schema` | `list_tables`, `list_columns`, `list_indexes`, `list_foreign_keys`, `list_views`, `get_full_schema` |
| `reflection` | `data` | `get_version`, `update_version`, `dump_table`, `rebuild_indexes`, `apply_batch`, `query_info_schema` |
| `rpcdispatch` | `domains` | `list`, `get`, `get_by_name`, `upsert`, `delete` |
| `rpcdispatch` | `subdomains` | `list`, `get`, `list_by_domain`, `upsert`, `delete` |
| `rpcdispatch` | `functions` | `list`, `get`, `list_by_subdomain`, `upsert`, `delete` |
| `rpcdispatch` | `models` | `list`, `get`, `get_by_name`, `upsert`, `delete` |
| `rpcdispatch` | `model_fields` | `list`, `get`, `list_by_model`, `upsert`, `delete` |
| `system` | `config` | `get`, `list`, `upsert`, `delete` |
| `system` | `conversations` | `insert`, `find_recent`, `insert_message`, `update_output`, `list_by_time`, `list_thread`, `list_channel_messages`, `list_recent`, `list_summary`, `get_stats`, `delete_by_thread`, `delete_before_timestamp` |
| `system` | `personas` | `get_by_name`, `list`, `upsert`, `delete`, `models_list`, `models_get_by_name`, `models_upsert`, `models_delete` |
| `system` | `public` | `get_home_links`, `get_navbar_routes`, `get_routes`, `upsert_route`, `delete_route` |
| `system` | `renewals` | `delete`, `get`, `list`, `upsert` |
| `system` | `roles` | `list`, `create`, `update`, `delete` |
| `system` | `scheduled_tasks` | `list_enabled_due_tasks`, `list_all_tasks`, `get_task`, `list_task_history`, `update_scheduled_task`, `create_scheduled_task_history`, `get_workflow_name_by_guid` |
| `system` | `workflows` | `get_active_workflow`, `count_active_runs_by_workflow_name`, `list_workflows`, `list_workflow_actions`, `create_workflow_run`, `get_workflow_run`, `list_workflow_runs`, `update_workflow_run`, `create_workflow_run_action`, `update_workflow_run_action`, `list_workflow_run_actions` |

## Current ownership map

| Domain | Subdomains | Query registry owner | Upstream module owners (imports) |
| --- | --- | --- | --- |
| `content` | `cache`, `indexing`, `pages`, `posts`, `wiki` | `queryregistry/content/handler.py` | `storage_module`, `public_gallery_module`, `public_users_module`, `content_pages_module`, `content_wiki_module` |
| `identity` | `audit`, `auth`, `enablements`, `mcp_agents`, `profiles`, `roles`, `sessions`, `users` | `queryregistry/identity/handler.py` | `auth_module`, `oauth_module`, `session_module`, `profile_module`, `role_module`, `role_admin_module`, `finance_module`, `mcp_gateway_module`, `user_admin_module` |
| `system` | `config`, `conversations`, `personas`, `public`, `renewals`, `roles`, `scheduled_tasks`, `workflows` | `queryregistry/system/handler.py` | `db_module`, `service_routes_module`, `conversations_module`, `openai_module`, `models_registry_module`, `scheduler_module`, `workflow_module`, `service_renewals_module`, plus supporting modules that read/write system config |
| `finance` | `accounts`, `credit_lots`, `credits`, `dimensions`, `journal_lines`, `journals`, `ledgers`, `numbers`, `periods`, `pipeline_config`, `product_journal_config`, `products`, `reporting`, `staging`, `staging_account_map`, `staging_invoices`, `staging_line_items`, `staging_purge_log`, `status`, `vendors` | `queryregistry/finance/handler.py` | `finance_module`; billing providers (`azure_cost_details_provider`, `azure_invoice_provider`); auth/credit consumers (`oauth_module`, `mcp_gateway_module`, `user_admin_module`) |
| `reflection` | `schema`, `data` | `queryregistry/reflection/handler.py` | `database_cli_module`, `rpcdispatch_module` |
| `rpcdispatch` | `domains`, `subdomains`, `functions`, `models`, `model_fields` | `queryregistry/rpcdispatch/handler.py` | `rpcdispatch_module`, `workflow_module` |
| `discord` | `guilds`, `channels` | `queryregistry/discord/handler.py` | `discord_bot_module`, `discord_chat_module`, `DiscordInputProvider` |
