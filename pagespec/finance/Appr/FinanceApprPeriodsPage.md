## Period Management
 
**Route:** `/finance/approver/periods`
 
*Close and reopen fiscal periods. The manager reviews period close readiness, closes periods when all blocking items are resolved, and can reopen closed periods for adjustments. Locking is an admin action — the manager controls the open/closed lifecycle.*
 
### Functional Activity
 
Period close is a formal accounting control that draws the line between "still working on it" and "the numbers are set." Closing a period prevents new journal entries from being created against it.
 
The close decision is the manager's — but the preparation is the accountant's. The accountant checks readiness on their side, resolves blockers (submitting draft journals, processing pending imports), and signals the manager. The manager then verifies and closes.
 
**When to use this page:**
- **End-of-period close:** At the end of each fiscal period, review readiness and close. In the 4-4-5 calendar this happens roughly every 4 weeks.
- **Close readiness check:** Run the blocker check before closing. Blockers include draft journals that haven't been submitted, pending journals that haven't been approved, and unprocessed staging imports. All blockers must be resolved before close.
- **Reopening for adjustments:** If an error is discovered after close but before admin lock, reopen the period, have the accountant make the correction, then re-close. This should be rare and documented.
 
**Period close workflow:**
1. Accountant resolves all blockers and notifies manager
2. Manager selects the period and runs the readiness check
3. If blockers remain, manager coordinates with accountant to resolve
4. If no blockers, manager approves the close → status moves from Open to Closed
5. Admin locks the period when no further adjustments are expected
 
### Page Layout
 
Year filter. Two sections: Open periods pending close (with "Review & Close" action per period expanding a readiness panel), and Closed periods (with Reopen action). Readiness panel shows either "Ready for close" with an Approve Close button, or a table of blocking items with type, name, and reason.
 
### Functions
 
#### `readPeriodStatus`
 
- **Request:** `ReadPeriodStatusParams1` — `{ fiscal_year: int | null }`
- **Response:** `ReadPeriodStatusList1` — `{ elements: ReadPeriodStatusElement1[] }`
- `ReadPeriodStatusElement1` — `{ period_guid: string, fiscal_year: int, period_number: int, period_name: string, start_date: string, end_date: string, period_status: int, draft_journals: int, pending_approval_journals: int, posted_journals: int, reversed_journals: int, closed_by: string | null, closed_on: string | null }`
 
#### `readCloseBlockers`
 
- **Request:** `ReadCloseBlockersParams1` — `{ guid: string }`
- **Response:** `ReadCloseBlockerList1` — `{ elements: ReadCloseBlockerElement1[] }`
- `ReadCloseBlockerElement1` — `{ period_guid: string, blocker_type: string, blocker_name: string, blocker_reason: string }`
 
#### `closePeriod`
 
- **Request:** `ClosePeriodParams1` — `{ guid: string }`
- **Response:** `ClosePeriodResult1` — `{ guid: string }`
 
#### `reopenPeriod`
 
- **Request:** `ReopenPeriodParams1` — `{ guid: string }`
- **Response:** `ReopenPeriodResult1` — `{ guid: string }`
 
### Notes
 
- Close/reopen is the manager's action. Lock/unlock is the admin's action on the Fiscal Calendar page.
- Journal counts in the period status response (draft, pending, posted, reversed) give the manager a quick view of whether the period still has unfinished work.
 
### Description
 
Period management page. Year-filtered view of open periods pending close and closed periods. Close readiness check identifies blocking items (unsubmitted journals, pending approvals, unprocessed imports). Manager approves close or coordinates blocker resolution. Closed periods can be reopened for adjustments before admin lock. Requires `ROLE_FINANCE_APPR`.
 