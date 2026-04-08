## Trial Balance & Period Readiness
 
**Route:** `/finance/accountant/balance`
 
*Period-scoped view of the General Ledger — account balances, transaction activity, and close readiness. Follows the summary + headers + detail pattern. This is where the accountant verifies that the books are balanced and that a period is ready for the manager to close.*
 
### Functional Activity
 
The trial balance is the fundamental accounting verification tool. It shows every GL account's total debits, total credits, and net balance for a fiscal period. If the GL is healthy, total debits equal total credits across all accounts and the net sums to zero. Any imbalance indicates an error that must be found and corrected before the period can close.
 
This page combines two views that answer the same underlying question — "are the books clean for this period?"
 
**Trial balance** answers: do the numbers add up? It shows account-level balances and highlights any imbalance.
 
**Period readiness** answers: is the work done? It checks for blocking items — draft journals that haven't been submitted, pending journals awaiting approval, unprocessed staging imports. Both checks must pass before the accountant can signal the manager that a period is ready for close.
 
**When to use this page:**
- **Ongoing verification:** Throughout the period, check the trial balance after posting journals to confirm the GL stays balanced. Catch errors early rather than discovering them at period close.
- **Pre-close preparation:** Before signaling the manager, run both the trial balance check and the readiness check. Resolve any imbalances (create correcting journal entries) and any blockers (submit draft journals, process pending imports).
- **Investigating account balances:** When a balance looks wrong, drill into the account to see which journals contributed to it. The detail view links to the Journals page filtered to that account and period.
- **Signaling the manager:** When the trial balance nets to zero and the readiness check shows no blockers, notify the manager that the period is ready for close.
 
**Typical end-of-period workflow:**
1. Select the fiscal year and period
2. Review the trial balance — verify total debits = total credits
3. If imbalanced, drill into suspect accounts to identify the problematic journals
4. Create correcting journal entries if needed, submit for approval
5. Check period readiness for blockers
6. Resolve any blockers (submit drafts, process imports)
7. Re-verify trial balance after corrections
8. Signal the manager that the period is ready
 
### Page Layout — Summary + Headers + Detail
 
**Summary:** Period selector (fiscal year + period). Displays aggregate trial balance totals (total debits, total credits, net — highlighted if non-zero), period readiness status (ready / N blockers), and quick counts of draft, pending, posted, and reversed journals for the period.
 
**Headers:** Account-level trial balance rows. Each row shows account number, account name, account type, total debits, total credits, and net balance for the selected period. Rows are sorted by account number. A totals row at the bottom shows the column sums. Clicking an account row navigates to the Journals page filtered to that account and period — showing the specific transactions that make up that balance.
 
**Readiness panel:** Expandable section (or integrated into the summary) showing close blockers when present — a table of blocker type, name, and reason. Shows "Ready for close" when no blockers remain.
 
### Functions
 
#### `readTrialBalance`
 
- **Request:** `ReadTrialBalanceParams1` — `{ fiscal_year: int | null, period_guid: string | null }`
- **Response:** `ReadTrialBalanceResult1` — `{ elements: ReadTrialBalanceElement1[] }`
- `ReadTrialBalanceElement1` — `{ period_guid: string, fiscal_year: int, period_number: int, period_name: string, account_guid: string, account_number: string, account_name: string, account_type: int, total_debit: string, total_credit: string, net_balance: string }`
 
*Returns one row per account that has posting activity in the selected period. Accounts with no activity are omitted.*
 
#### `readPeriodStatus`
 
- **Request:** `ReadPeriodStatusParams1` — `{ fiscal_year: int | null }`
- **Response:** `ReadPeriodStatusList1` — `{ elements: ReadPeriodStatusElement1[] }`
- `ReadPeriodStatusElement1` — `{ period_guid: string, fiscal_year: int, period_number: int, period_name: string, period_status: int, draft_journals: int, pending_approval_journals: int, posted_journals: int, reversed_journals: int }`
 
*Provides journal counts per period for the summary panel and period selector.*
 
#### `readCloseBlockers`
 
- **Request:** `ReadCloseBlockersParams1` — `{ guid: string }`
- **Response:** `ReadCloseBlockerList1` — `{ elements: ReadCloseBlockerElement1[] }`
- `ReadCloseBlockerElement1` — `{ period_guid: string, blocker_type: string, blocker_name: string, blocker_reason: string }`
 
*Returns an empty list when the period is ready for close. Same function used by the manager's Period Management page.*
 
### Notes
 
- The trial balance is a read-only reporting view — the accountant cannot edit GL balances directly. Corrections are made by creating journal entries on the Journals page.
- Drilling into a header row (clicking an account) navigates to the Journals page with filters pre-set to show journals containing lines that post to that account in the selected period. This is cross-page navigation, not an in-page detail panel.
- The same `readTrialBalance` data was previously displayed on both the Accountant and Manager pages. In the realignment, this is the accountant's primary reporting surface. The manager sees period-level journal activity on the Approvals Workbench summary panel, which provides sufficient oversight without a dedicated trial balance page.
 
### Description
 
Trial balance and period close readiness page following the summary + headers + detail pattern. Summary shows aggregate debit/credit/net totals and readiness status for the selected period. Headers list account-level balances. Drilling into an account navigates to the Journals page filtered to that account. Readiness panel shows close blockers. The accountant's primary tool for verifying GL integrity and preparing periods for close. Requires `ROLE_FINANCE_ACCT`.
 