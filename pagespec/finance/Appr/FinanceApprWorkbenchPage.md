## Approvals Workbench
 
**Route:** `/finance/approver/workbench`
 
*Unified approval surface for the accounting manager. Follows the summary + headers + detail pattern. The manager reviews, approves, or rejects items submitted by the accountant — staging imports that need authorization before promotion into journals, and journals that need authorization before posting to the GL.*
 
### Functional Activity
 
The workbench is the manager's primary operational page. Everything the accountant submits flows through here. The two approval types represent the two SoD gates in the finance pipeline:
 
**Import approval** is the first gate. When the accountant pulls billing data from vendor APIs (Azure cost details, invoices), the raw data lands in staging. The accountant reviews it and submits for approval. The manager verifies the data looks correct — right vendor, right amounts, right date range — and either approves (enabling promotion into a journal) or rejects with a reason.
 
**Journal approval** is the second gate. Whether a journal was created manually by the accountant or generated automatically by the promote pipeline, it must be approved before it posts to the GL. The manager verifies that debits equal credits, account assignments are correct, and the journal belongs to the right period. Approving a journal posts it — this is the moment the numbers hit the books.
 
The summary panel provides period-scoped context: total journal activity, balance totals, and pending counts for the selected period. This lets the manager evaluate individual items against the period's overall financial position.
 
**When to use this page:**
- **Daily review:** Check for pending items. Staging imports and journals awaiting approval block the accountant's workflow — timely review keeps the pipeline moving.
- **Import review:** Drill into import line items, verify amounts and vendor data, approve or reject.
- **Journal review:** Drill into journal lines, verify debit/credit balance and account assignments, approve or reject.
- **Period overview:** Use the summary panel to see the full picture of journal activity and posted balances for a period before approving individual items.
 
**Import approval flow:**
1. Accountant imports billing data → status: Pending
2. Accountant submits for approval → status: Pending Approval
3. Manager reviews here → Approve (status → Approved, accountant can promote) or Reject with reason (status → Rejected)
 
**Journal approval flow:**
1. Accountant creates journal → status: Draft
2. Accountant submits for approval → status: Pending
3. Manager reviews here → Approve (journal posts to GL, status → Posted) or Reject with reason (status → Draft, accountant can correct and resubmit)
 
### Page Layout — Summary + Headers + Detail
 
**Summary:** Period selector (fiscal year + period). Displays pending import count, pending journal count, and posted journal activity for the selected period — total posted journals, total debits, total credits, draft count, reversed count. This replaces the former separate Journal Summary tab.
 
**Headers:** Pending imports and pending journals listed together or in two collapsible sections. Each row shows enough metadata to identify the item without drilling in.
 
**Detail — Import:** Line items table with date, vendor, service, category, description, amount, currency. Approve and Reject (with reason dialog) actions.
 
**Detail — Journal:** Journal header metadata (posting key, source type, period, status) with lines table showing line number, account, description, debit, credit. Approve and Reject (with reason dialog) actions.
 
### Functions
 
#### `readApprovalSummary`
 
- **Request:** `ReadApprovalSummaryParams1` — `{ fiscal_year: int | null, periods_guid: string | null }`
- **Response:** `ReadApprovalSummaryResult1` — `{ pending_imports: int, pending_journals: int, draft_journals: int, posted_journals: int, reversed_journals: int, total_debit: string, total_credit: string }`
 
#### `readPendingImports`
 
- **Request:** `ReadPendingImportsParams1` — `{ status: int | null }`
- **Response:** `ReadPendingImportList1` — `{ elements: ReadPendingImportElement1[] }`
- `ReadPendingImportElement1` — `{ recid: int, source: string, scope: string | null, metric: string, period_start: string, period_end: string, row_count: int, status: int, status_name: string, requested_by: string | null, created_on: string }`
 
#### `readImportLineItems`
 
- **Request:** `ReadImportLineItemsParams1` — `{ imports_recid: int }`
- **Response:** `ReadImportLineItemList1` — `{ elements: ReadImportLineItemElement1[] }`
- `ReadImportLineItemElement1` — `{ recid: int, vendor_name: string | null, date: string | null, service: string | null, category: string | null, description: string | null, amount: string, currency: string | null }`
 
#### `approveImport`
 
- **Request:** `ApproveImportParams1` — `{ imports_recid: int }`
- **Response:** `ApproveImportResult1` — `{ imports_recid: int, approved: bool }`
 
#### `rejectImport`
 
- **Request:** `RejectImportParams1` — `{ imports_recid: int, reason: string | null }`
- **Response:** `RejectImportResult1` — `{ imports_recid: int, rejected: bool }`
 
#### `readPendingJournals`
 
- **Request:** `ReadPendingJournalsParams1` — `{ journal_status: int | null, fiscal_year: int | null, periods_guid: string | null }`
- **Response:** `ReadPendingJournalList1` — `{ elements: ReadPendingJournalElement1[] }`
- `ReadPendingJournalElement1` — `{ recid: int, name: string, description: string | null, posting_key: string | null, source_type: string | null, period_name: string | null, status: int, status_name: string, line_count: int, total_debit: string, total_credit: string, posted_by: string | null, created_on: string }`
 
#### `readJournalLines`
 
- **Request:** `ReadJournalLinesParams1` — `{ journals_recid: int }`
- **Response:** `ReadJournalLineList1` — `{ elements: ReadJournalLineElement1[] }`
- `ReadJournalLineElement1` — `{ recid: int, line_number: int, account_number: string, account_name: string, debit: string, credit: string, description: string | null, dimensions: string[] }`
 
#### `approveJournal`
 
- **Request:** `ApproveJournalParams1` — `{ recid: int }`
- **Response:** `ApproveJournalResult1` — `{ recid: int, status: int }`
 
#### `rejectJournal`
 
- **Request:** `RejectJournalParams1` — `{ recid: int, reason: string | null }`
- **Response:** `RejectJournalResult1` — `{ recid: int, status: int }`
 
### Notes
 
- This page supersedes the former "Approval Queue," "Journal Review," and "Journal Summary" tabs. The summary panel provides the period-level journal activity view that Journal Summary previously offered as a standalone tab.
- The `readPendingJournals` function with `journal_status: null` and period filters provides the same data the former Journal Summary tab displayed — no separate reporting function needed.
 
### Description
 
Unified approvals workbench following the summary + headers + detail pattern. Summary shows period-scoped journal activity and pending counts. Headers list pending staging imports and pending journals. Detail drills into line items with approve/reject actions. Supersedes the former Journal Summary tab by incorporating period-level journal activity into the summary panel. Requires `ROLE_FINANCE_APPR`.
 