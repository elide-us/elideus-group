## Chart of Accounts
 
**Route:** `/finance/admin/accounts`
 
*Define the GL account structure — the foundation that all journal entries post against. Every debit and credit in the system targets an account defined here.*
 
### Functional Activity
 
The chart of accounts is the classification structure for all financial data. Each account has a number (the human-readable identifier used in reports), a name, and a type that determines how the account behaves in financial statements.
 
**When to use this page:**
- **Initial setup:** Before any journals can be created, the chart of accounts must be populated with at least the essential posting accounts (cash, revenue, expense categories). A typical small organization needs 20-50 accounts; this system currently operates with ~15.
- **Adding new accounts:** When a new category of expense or revenue arises, create a new posting account. For example, adding a new cloud vendor might require a new expense account for that vendor's costs.
- **Account hierarchy:** Non-posting (summary) accounts can be created as parent nodes for reporting rollups. The `parent` field links child accounts to their summary parent. Posting accounts are the leaf nodes that receive actual journal entries.
- **Deactivation:** Set status to inactive to prevent future postings. Historical data on the account remains.
 
**Account types and their financial statement role:**
- **Asset (0):** Resources owned — cash, receivables, prepaid expenses. Normal debit balance.
- **Liability (1):** Obligations owed — payables, accrued expenses, deferred revenue. Normal credit balance.
- **Equity (2):** Owner's stake — retained earnings, contributed capital. Normal credit balance.
- **Revenue (3):** Income earned — credit sales, service fees, enablement revenue. Normal credit balance.
- **Expense (4):** Costs incurred — cloud hosting, subscriptions, API usage. Normal debit balance.
 
**Typical workflow:**
1. Create summary (non-posting) accounts for major categories: Assets, Liabilities, Equity, Revenue, Expenses
2. Create posting accounts under each summary for specific line items: Cash, Azure Hosting, OpenAI API Costs, Credit Revenue, etc.
3. Set the `is_posting` flag to true for accounts that will receive journal entries
4. Reference account numbers in the account mapping page to configure automated billing import classification
 
### Page Layout
 
Inline form at top for create/edit with account number, name, type dropdown, and save button. Table below showing all accounts with edit and delete buttons.
 
### Lookup: Account Types
 
| Value | Label | Normal Balance |
|---|---|---|
| 0 | Asset | Debit |
| 1 | Liability | Credit |
| 2 | Equity | Credit |
| 3 | Revenue | Credit |
| 4 | Expense | Debit |
 
### Functions
 
#### `readAccounts`
 
- **Request:** none
- **Response:** `ReadAccountList1` — `{ elements: ReadAccountElement1[] }`
- `ReadAccountElement1` — `{ guid: string | null, number: string, name: string, account_type: int, parent: string | null, is_posting: bool, status: int }`
 
#### `upsertAccount`
 
- **Request:** `UpsertAccountParams1` — `{ guid: string | null, number: string, name: string, account_type: int, parent: string | null, is_posting: bool, status: int }`
- **Response:** `UpsertAccountResult1` — `{ guid: string, number: string, name: string }`
 
*Updates if `guid` is provided, inserts if null. GUID is generated server-side on insert.*
 
#### `deleteAccount`
 
- **Request:** `DeleteAccountParams1` — `{ guid: string }`
- **Response:** `DeleteAccountResult1` — `{ guid: string }`
 
*Deleting an account with posted journal lines should be prevented server-side — accounts with transaction history cannot be removed, only deactivated.*
 
### Notes
 
- `readAccounts` is the most widely shared lookup in the finance module — used by Ledgers (CoA root dropdown), Account Mappings (posting account assignment), Number Sequences (parent account binding), and the Accountant's journal creation form.
- Account numbers are free-text strings, not auto-generated — the admin chooses the numbering scheme (e.g., 1000-series for assets, 4000-series for expenses).
- The `parent` field enables hierarchical rollup reporting but is not currently enforced in the UI tree view — it's stored for future use.
- Only posting accounts appear in the journal line account dropdown and account mapping target dropdown. Non-posting accounts are summary/reporting nodes.
 
### Description
 
Chart of accounts management page. Inline form for create/edit with account number, name, type (Asset, Liability, Equity, Revenue, Expense), parent account, posting flag, and status. Table displays all accounts with type label, status, and edit/delete controls. Accounts are the foundational reference for all journal entries, account mappings, and financial reporting. Requires `ROLE_FINANCE_ADMIN`.