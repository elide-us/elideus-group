## Billing Import
 
**Route:** `/finance/accountant/imports`
 
*Review staged billing data and promote approved imports into journal entries. Staging data is populated by the accounting manager or by automation workflows that pull cost and invoice data from vendor APIs. The accountant's job is to review what's been staged, promote approved batches into journals, and submit those journals for approval.*
 
### Functional Activity
 
This page is the accountant's window into the billing-to-GL pipeline. The accountant does not initiate the raw data pull — that's either automated via scheduled tasks or triggered by the manager. By the time data appears here, it has already been imported into staging and is working through the approval lifecycle.
 
The accountant's responsibilities on this page:
- Review staged import batches and their line items to verify the data looks correct
- Promote approved imports into journal entries — this runs the classify-and-journal-create pipeline
- Monitor promotion progress and handle classification failures
- Delete imports that are incorrect, duplicated, or abandoned
 
**Billing-to-GL pipeline (the accountant's view):**
1. Staged data arrives (via automation or manager action) → status: Pending
2. Manager reviews and approves on the Approvals Workbench → status: Approved
3. Accountant selects the approved import here, chooses a ledger, and promotes → pipeline runs
4. Pipeline classifies costs using account mappings, creates a draft journal → status: Promoted
5. Accountant reviews the generated journal on the Journals page and submits for approval
6. Manager approves the journal on the Workbench → journal posts to GL
 
**When to use this page:**
- **Reviewing staged data:** Check what's been imported, drill into line items to verify vendor charges, amounts, and date ranges.
- **Promoting approved imports:** After the manager approves an import, come here to promote it. Select the target ledger (or use the default), trigger the promote pipeline, and monitor progress.
- **Handling classification failures:** If the promote pipeline fails at the classify step, it means a line item's service/meter combination doesn't match any account mapping. Coordinate with the admin to add the missing mapping, then retry.
- **Cleanup:** Delete imports that were test runs, duplicates, or that were rejected and won't be resubmitted.
 
### Page Layout
 
Import list table showing all staged batches with source, metric, date range, row count, status, requested by, approved by, and actions. Clicking a row expands or navigates to the line items for that import. Ledger selector and Promote button for acting on approved imports. Pipeline progress panel shows step-by-step status during promotion (validate → classify → create journal → mark promoted). Delete action available on non-promoted imports.
 
### Functions
 
#### `readImports`
 
- **Request:** `ReadImportsParams1` — `{ status: int | null }`
- **Response:** `ReadImportList1` — `{ elements: ReadImportElement1[] }`
- `ReadImportElement1` — `{ recid: int, source: string, scope: string | null, metric: string, period_start: string, period_end: string, row_count: int, status: int, status_name: string, error: string | null, requested_by: string | null, approved_by: string | null, approved_on: string | null, created_on: string }`
 
*Pass `status: null` for all imports.*
 
#### `readImportLineItems`
 
- **Request:** `ReadImportLineItemsParams1` — `{ imports_recid: int }`
- **Response:** `ReadImportLineItemList1` — `{ elements: ReadImportLineItemElement1[] }`
- `ReadImportLineItemElement1` — `{ recid: int, vendor_name: string | null, date: string | null, service: string | null, category: string | null, description: string | null, quantity: string | null, unit_price: string | null, amount: string, currency: string | null }`
 
#### `promoteImport`
 
- **Request:** `PromoteImportParams1` — `{ imports_recid: int, ledgers_recid: int | null }`
- **Response:** `PromoteImportResult1` — `{ task_guid: string }`
 
*Triggers the promote pipeline as an async workflow. Returns a task GUID for progress tracking. Pass `ledgers_recid: null` for automatic ledger assignment.*
 
#### `deleteImport`
 
- **Request:** `DeleteImportParams1` — `{ imports_recid: int }`
- **Response:** `DeleteImportResult1` — `{ imports_recid: int, deleted: bool }`
 
*Cannot delete promoted imports — they are linked to generated journals.*
 
### Shared Lookups
 
- `readLedgers` — populates the ledger selector dropdown for promotion
 
### Notes
 
- Import status flow: Pending (0) → Pending Approval (4) → Approved (1) / Rejected (5) → Promoted (3). Failed (2) indicates an import that errored during execution. The accountant sees all statuses but can only promote Approved imports.
- The promote pipeline is an async workflow — the frontend polls the task for step-by-step progress. Classification failures are the most common error and are resolved by adding account mappings on the Admin page.
- The import trigger functions (cost detail import, invoice import) are manager/automation actions, not surfaced on this page. The accountant works with data that has already been staged.
 
### Description
 
Billing import review and promotion page. Table of staged import batches with drill-down to line items. Promote action triggers the classify-and-journal-create pipeline for approved imports. Pipeline progress tracking with step-by-step status. Delete available for non-promoted imports. Requires `ROLE_FINANCE_ACCT`.
 