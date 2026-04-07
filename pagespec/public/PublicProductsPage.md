# Products & Services

**Route:** `/products`

*Public-facing product catalog and purchase page. Products are managed via the finance module (future products management page). This page is the consumer-facing storefront.*

## Table: `finance_products`

| Column | Type | Notes |
|---|---|---|
| `recid` | BIGINT IDENTITY(1,1) | PK |
| `element_sku` | NVARCHAR(32) | Number-sequence-derived SKU (e.g. `340001000001`), unique |
| `element_name` | NVARCHAR(200) | Display name |
| `element_description` | NVARCHAR(512) | Product description, nullable |
| `product_categories_recid` | BIGINT | FK → `finance_product_categories.recid` |
| `element_currency_price` | DECIMAL(19,5) | Price in currency, default `0` |
| `element_credit_price` | INT | Price in credits, default `0` |
| `element_currency_type` | NVARCHAR(3) | ISO currency code (e.g. `USD`) |
| `element_is_recurring` | BIT | Subscription purchase flag, default `0` |
| `element_status` | BIGINT | FK → status lookup (coming soon, available, out of stock, etc.) |
| `element_created_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |
| `element_modified_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |

*SKU is derived from number sequences (e.g. format `PROD_1`): account number + sequence + six-digit serial. Number sequences and formats are defined elsewhere in the finance module, only referenced here.*

## Lookup Table: `finance_product_categories`

| Column | Type | Notes |
|---|---|---|
| `recid` | BIGINT IDENTITY(1,1) | PK |
| `element_name` | NVARCHAR(64) | Category name (e.g. `enablement`, `credit_purchase`) |

## Functions

### `readProducts`

- **Request:** none
- **Response:** `ReadProductList1` — `{ elements: ReadProductElement1[] }`
- `ReadProductElement1` — `{ recid: int, sku: string, name: string, description: string | null, category_name: string, currency_price: string, credit_price: int, currency_type: string, is_recurring: bool, status_name: string }`

### `purchaseProduct`

- **Request:** `PurchaseProductParams1` — `{ recid: int }`
- **Response:** `PurchaseProductResult1` — `{ transaction_token: string, credits_granted: int | null, enablement_granted: string | null, lot_number: string | null }`

### `readWalletBalance`

- **Request:** none
- **Response:** `ReadWalletBalanceResult1` — `{ credits: int }`

*Wallet balance may come from the existing `users:profile` subdomain or be broken out as a dedicated function — TBD during rebuild.*

## Notes

- This is a **read-only catalog** from the customer's perspective. Product CRUD is managed in the finance module (future products management page in the finance admin area).
- `category_name` and `status_name` are denormalized display fields resolved from FK joins.
- Purchase flow triggers backend side effects: credit lot creation, enablement grants, journal entries via the finance pipeline. These are backend concerns, not detailed here.
- Product management CRUD functions (`createProduct`, `updateProduct`, `deleteProduct`) will be defined in a separate finance admin page spec.

## Description

Page displays available products grouped by category in a card layout. Shows wallet balance. Each product card displays name, SKU, description, currency price, credit price, and status. Purchase flow uses a cart component (TBD). Uses the application theme.