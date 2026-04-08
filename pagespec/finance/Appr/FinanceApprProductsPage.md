## Product Management
 
**Route:** `/finance/approver/products`
 
*Manage the product catalog and configure how product purchases flow into the general ledger. This page combines product definition (what users can buy), product journal configuration (which journal receives purchase postings for each product category and period), and the approval lifecycle for journal configurations.*
 
### Functional Activity
 
Products are the purchasable items offered through the storefront — credit packages, enablements, and subscriptions. This page defines what products exist, how they're priced, and how the revenue from their purchase is recorded in the GL.
 
The page has two areas of concern:
 
**Product catalog management** defines the items themselves — SKU, name, price, credit amount, enablement key, recurring flag. This is the business definition of what users can buy. Products are consumed by the public storefront page and the credit lot system.
 
**Product journal configuration** defines where the money goes. Each product category needs to be linked to a specific GL journal within a fiscal period, so that when a purchase occurs, the system knows which journal to post the revenue entry to. Configurations follow a lifecycle: the manager creates a config (Draft), approves it (Approved), then the admin activates it (Active) on the Admin's Pipeline Config page. The manager can close an active config when the period ends.
 
**When to use this page:**
- **Adding products:** When the organization offers a new credit package or enablement, create the product here with its pricing, credit amount, and enablement key. The product appears on the public storefront once active.
- **Price changes:** Update pricing, credit amounts, or descriptions on existing products. Changes take effect immediately on the storefront.
- **Period journal setup:** At the start of each fiscal period, create a product journal configuration linking each product category to the appropriate journal for that period. This must be done before any purchases can be recorded for the new period.
- **Configuration lifecycle:** Create (Draft) → Approve (Approved) → Admin activates (Active) → Close (Closed) when the period ends. The manager handles create, approve, and close. The admin handles activation as a SoD control.
 
**Product journal configuration workflow:**
1. Accountant creates a journal for the new period (on the Accountant's Journals page)
2. Manager navigates here, creates a product journal config linking the product category to that journal and period
3. Manager approves the config → status moves to Approved
4. Admin activates the config on the Admin page → status moves to Active
5. Purchases for that category now post to the configured journal
6. At period end, manager closes the config → status moves to Closed
 
**Product categories:**
- `credit_purchase` — Credit packages that add credits to a user's wallet
- `enablement` — Feature unlocks (e.g., storage access, OpenAI generation, LumaAI video)
 
### Page Layout
 
Two sections:
 
**Product Catalog:** Table of products with create button. Create/edit via dialog with SKU, name, description, category, price, currency, credits, enablement key, recurring flag, sort order, and status. Delete with confirmation.
 
**Journal Configuration:** Create form with category, journal scope, period dropdown, and journal dropdown. Table of existing configurations showing category, journal scope, journal name, period, status, approved by, and actions (Approve for Draft, Close for Active).
 
### Functions — Product Catalog
 
#### `readProducts`
 
- **Request:** `ReadProductsParams1` — `{ category: string | null, status: int | null }`
- **Response:** `ReadProductList1` — `{ elements: ReadProductElement1[] }`
- `ReadProductElement1` — `{ guid: string, sku: string, name: string, description: string | null, category: string, price: string, currency: string, credits: int, enablement_key: string | null, is_recurring: bool, sort_order: int, status: int }`
 
#### `createProduct`
 
- **Request:** `CreateProductParams1` — `{ sku: string, name: string, description: string | null, category: string, price: string, currency: string, credits: int, enablement_key: string | null, is_recurring: bool, sort_order: int }`
- **Response:** `CreateProductResult1` — `{ guid: string, sku: string }`
 
*GUID is generated server-side (non-deterministic). Created with status active by default.*
 
#### `updateProduct`
 
- **Request:** `UpdateProductParams1` — `{ guid: string, name: string, description: string | null, price: string, currency: string, credits: int, enablement_key: string | null, is_recurring: bool, sort_order: int, status: int }`
- **Response:** `UpdateProductResult1` — `{ guid: string, sku: string }`
 
*SKU and category are immutable after creation — SKU is the permanent business identifier, category determines the product journal config binding. All other fields are editable.*
 
#### `deleteProduct`
 
- **Request:** `DeleteProductParams1` — `{ guid: string }`
- **Response:** `DeleteProductResult1` — `{ guid: string }`
 
### Functions — Journal Configuration
 
#### `readProductJournalConfigs`
 
- **Request:** `ReadProductJournalConfigsParams1` — `{ category: string | null, periods_guid: string | null, status: int | null }`
- **Response:** `ReadProductJournalConfigList1` — `{ elements: ReadProductJournalConfigElement1[] }`
- `ReadProductJournalConfigElement1` — `{ recid: int, category: string, journal_scope: string, journals_recid: int, journal_name: string | null, periods_guid: string, period_name: string | null, approved_by: string | null, approved_on: string | null, activated_by: string | null, activated_on: string | null, status: int, status_name: string }`
 
*`journal_name` and `period_name` are denormalized display fields.*
 
#### `createProductJournalConfig`
 
- **Request:** `CreateProductJournalConfigParams1` — `{ category: string, journal_scope: string, journals_recid: int, periods_guid: string }`
- **Response:** `CreateProductJournalConfigResult1` — `{ recid: int, status: int }`
 
*Creates in Draft status.*
 
#### `approveProductJournalConfig`
 
- **Request:** `ApproveProductJournalConfigParams1` — `{ recid: int }`
- **Response:** `ApproveProductJournalConfigResult1` — `{ recid: int, status: int }`
 
*Manager approves → status moves from Draft to Approved. Admin activates on their page.*
 
#### `closeProductJournalConfig`
 
- **Request:** `CloseProductJournalConfigParams1` — `{ recid: int }`
- **Response:** `CloseProductJournalConfigResult1` — `{ recid: int, status: int }`
 
*Manager closes an active config at period end → status moves to Closed.*
 
### Shared Lookups
 
- `readPeriods` — populates the period dropdown in the journal config form (filtered to open periods)
- `readJournals` — populates the journal dropdown (filtered to draft journals for the selected period)
 
### Notes
 
- Product journal configuration has a multi-role lifecycle: Manager creates/approves/closes, Admin activates. The activation step is a SoD control — the admin's Pipeline Config or a dedicated activation action on the Admin side.
- Only one active configuration per category per period is expected. Activating a new config for the same category/period should close the previous one (server-side enforcement).
- `enablement_key` links a product to a security enablement entry (e.g., `ENABLE_OPENAI`). Purchasing the product grants the enablement to the user.
- SKU generation uses number sequences — the manager should ensure a product SKU sequence exists before creating products that need auto-generated SKUs.
 
### Description
 
Product management page combining product catalog CRUD and product journal configuration lifecycle. Products section: dialog form for create/edit with SKU, name, description, category, pricing, credits, enablement key, recurring flag, and status. Journal config section: create form linking product categories to journals per fiscal period, with approve and close lifecycle actions. The manager defines products and configures how purchase revenue flows into the GL. Requires `ROLE_FINANCE_APPR`.
 