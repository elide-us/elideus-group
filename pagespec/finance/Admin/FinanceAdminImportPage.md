## Import Staging
 
**Route:** `/finance/admin/imports`
 
*Configure key-value parameters that control the runtime behavior of financial pipelines — billing import, credit purchase, and credit consumption. These settings define which GL accounts the pipelines use, what source type strings they stamp, and what default dimensions they apply.*
 
### Functional Activity
 
Pipeline configs are the wiring between automated financial operations and the chart of accounts. When a billing import is promoted, when a user purchases credits, or when credits are consumed by a service call, the corresponding pipeline reads its configuration from this table to know which accounts to debit and credit.
 
This is purely a reference table — the pipelines read from it at execution time. Changing a value here immediately affects the next pipeline execution. There is no approval workflow on config changes; they take effect as soon as saved.
 
**When to use this page:**
- **Initial setup:** After the chart of accounts is created, populate the pipeline configs so the pipelines know which accounts to use. Without these configs, automated journal creation will fail.
- **Account reassignment:** If the organization restructures its chart of accounts (e.g., splitting a single expense account into multiple sub-accounts), update the relevant pipeline configs to point to the new account numbers.
- **New pipeline setup:** When a new automated pipeline is added (e.g., a future enablement purchase pipeline), add its config entries here.
 
**Current pipelines and their configs:**
 
**`billing_import`** — Controls how Azure billing data is promoted into journals:
- `ap_account_number` — The accounts payable contra account credited when billing expenses are recorded (e.g., 2200)
- `default_dimension_recids` — JSON array of dimension recids auto-applied to every billing import journal line (e.g., [15, 4] for Project=TheOracleRPC + Department=Engineering)
- `source_type_invoice` — Source type string stamped on invoice-type imports (e.g., "azure_invoice")
- `source_type_usage` — Source type string stamped on usage/cost-type imports (e.g., "azure_billing_import")
 
**`credit_purchase`** — Controls the journal entries created when a user buys credits:
- `cash_account_number` — Cash account debited (e.g., 1100)
- `deferred_revenue_account_number` — Deferred revenue account credited (e.g., 2100)
- `payment_clearing_account_number` — Payment processor clearing account (e.g., 1300)
- `merchant_fee_account_number` — Merchant fee expense account for processor fees (e.g., 5010)
 
**`credit_consumption`** — Controls the journal entries created when credits are consumed:
- `deferred_revenue_account_number` — Deferred revenue account debited to recognize revenue (e.g., 2100)
- `revenue_account_number` — Revenue account credited (e.g., 4010)
 
**Typical workflow:**
1. Create the chart of accounts with the required accounts (cash, AP, deferred revenue, revenue, expenses)
2. Create dimensions for default tagging
3. Navigate to this page and create config entries for each pipeline, referencing the account numbers and dimension recids from steps 1-2
4. Test by running a billing import promote or credit purchase and verifying the generated journal entries hit the correct accounts
 
### Page Layout
 
Pipeline filter dropdown (optional — show all, or filter to a specific pipeline). Table showing all config entries with pipeline, key, value, description, status, and edit/delete actions. Inline or collapsible create/edit form with pipeline name, key, value, description, and status.
 
### Functions
 
#### `readPipelineConfigs`
 
- **Request:** `ReadPipelineConfigsParams1` — `{ pipeline: string | null }`
- **Response:** `ReadPipelineConfigList1` — `{ elements: ReadPipelineConfigElement1[] }`
- `ReadPipelineConfigElement1` — `{ recid: int | null, pipeline: string, key: string, value: string, description: string | null, status: int, created_on: string | null, modified_on: string | null }`
 
*Pass `pipeline: null` to list all configs across all pipelines.*
 
#### `getPipelineConfig`
 
- **Request:** `GetPipelineConfigParams1` — `{ pipeline: string, key: string }`
- **Response:** `GetPipelineConfigResult1` — same shape as `ReadPipelineConfigElement1`
 
*Lookup a specific config entry by pipeline + key composite.*
 
#### `upsertPipelineConfig`
 
- **Request:** `UpsertPipelineConfigParams1` — `{ recid: int | null, pipeline: string, key: string, value: string, description: string | null, status: int }`
- **Response:** `UpsertPipelineConfigResult1` — same shape as `ReadPipelineConfigElement1`
 
*Updates if `recid` is provided, inserts if null. The `pipeline + key` composite is the natural key.*
 
#### `deletePipelineConfig`
 
- **Request:** `DeletePipelineConfigParams1` — `{ recid: int }`
- **Response:** `DeletePipelineConfigResult1` — `{ recid: int, deleted: bool }`
 
### Notes
 
- Pipeline config values are plain strings — the consuming pipeline is responsible for parsing (e.g., `default_dimension_recids` is stored as a JSON array string and parsed at runtime).
- Account numbers in config values reference `finance_accounts.element_number`, not GUIDs — the pipeline resolves the account GUID from the number at execution time.
- There is no validation on save that the referenced account numbers actually exist in the chart of accounts. Invalid references will cause pipeline execution failures at runtime. This is intentional — it allows pre-configuring accounts that will be created later.
- Config entries have a status flag but pipelines currently do not filter by status — all entries are read regardless. The status flag is reserved for future use (e.g., allowing a config to be disabled without deletion).
- This page had no frontend tab in the former FinanceAdminPage — it is new in the rebuild. The `finance:pipeline_config` RPC subdomain existed and was used by the backend pipelines, but configuration was done directly in the database.
 
### Description
 
Pipeline configuration page. Key-value settings that control which GL accounts and default dimensions the automated financial pipelines use at execution time. Three pipelines: billing import (AP contra account, default dimensions, source type strings), credit purchase (cash, deferred revenue, clearing, merchant fee accounts), and credit consumption (deferred revenue, revenue accounts). Filterable by pipeline, table with edit/delete, inline create/edit form. Changes take effect immediately on the next pipeline execution. Requires `ROLE_FINANCE_ADMIN`.
 