## Ledger Management
 
**Route:** `/finance/admin/ledgers`
 
*Create and manage the General Ledger and any future reporting ledgers. A ledger is the top-level container for all journal entries — it must exist before any journals can be created.*
 
### Functional Activity
 
A ledger defines a posting destination for journal entries. Most organizations need exactly one General Ledger. Additional ledgers are used for reporting currencies, statutory reporting, or analytical ledgers that receive copies of postings from the primary GL.
 
**When to use this page:**
- **Initial setup:** Create the General Ledger as the first step in finance module configuration. Without a ledger, no journals can be created.
- **Multi-ledger scenarios:** Create additional ledgers when the organization needs to maintain parallel books (e.g., a USD reporting ledger alongside a functional currency ledger).
- **Deactivation:** Set a ledger to Inactive to prevent new journals from posting to it. Existing posted journals remain — this is a forward-looking gate, not a retroactive deletion.
- **Chart of accounts binding:** Each ledger can be optionally bound to a root account in the chart of accounts, which scopes which accounts are available for posting within that ledger.
 
**Typical workflow:**
1. Create the General Ledger with a name and optional description
2. Optionally bind it to a chart of accounts root (if using account scoping)
3. Verify the ledger appears in the Accountant's journal creation dropdown
4. Never delete an active ledger with posted journals
 
### Page Layout
 
Table of ledgers with create button. Create/edit via dialog form. Delete with confirmation (marks inactive).
 
### Functions
 
#### `readLedgers`
 
- **Request:** none
- **Response:** `ReadLedgerList1` — `{ elements: ReadLedgerElement1[] }`
- `ReadLedgerElement1` — `{ recid: int, name: string, description: string | null, chart_of_accounts_guid: string | null, status: int, created_on: string | null, modified_on: string | null }`
 
#### `createLedger`
 
- **Request:** `CreateLedgerParams1` — `{ name: string, description: string | null, chart_of_accounts_guid: string | null }`
- **Response:** `CreateLedgerResult1` — `{ recid: int, name: string }`
 
#### `updateLedger`
 
- **Request:** `UpdateLedgerParams1` — `{ recid: int, name: string, description: string | null, chart_of_accounts_guid: string | null, status: int }`
- **Response:** `UpdateLedgerResult1` — `{ recid: int, name: string }`
 
#### `deleteLedger`
 
- **Request:** `DeleteLedgerParams1` — `{ recid: int }`
- **Response:** `DeleteLedgerResult1` — `{ recid: int }`
 
*Delete sets status to Inactive rather than removing the row — ledgers with posted journals cannot be destroyed.*
 
### Shared Lookups
 
- `readAccounts` — populates the "Chart of accounts root" dropdown in the create/edit dialog
 
### Description
 
Ledger management page. Dialog form for create/edit with name, description, chart of accounts root (account dropdown), and status toggle (edit only). Table displays all ledgers with status chip, description, creation date, and edit/delete actions. Delete marks inactive. Requires `ROLE_FINANCE_ADMI