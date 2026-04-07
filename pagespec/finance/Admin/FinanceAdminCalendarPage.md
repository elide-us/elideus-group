## Fiscal Calendar
 
**Route:** `/finance/admin/calendar`
 
*Generate and manage fiscal periods using the 4-4-5 pattern. The admin generates fiscal years, views period status summaries, and locks/unlocks closed periods. Period close is a manager action — the admin controls the permanent lock.*
 
### Functional Activity
 
The fiscal calendar defines the time boundaries for all financial transactions. Every journal must be assigned to a fiscal period. The 4-4-5 pattern creates 12 standard 28-day periods and 4 closing weeks per fiscal year, providing consistent period lengths for month-over-month comparisons.
 
**When to use this page:**
- **Annual setup:** At the start of each fiscal year, generate the next year's periods. This should be done before the first day of the new year so that journals can be created against it. Periods for future years can be generated in advance.
- **Period status review:** Monitor which periods are open, closed, or locked across all fiscal years. The summary cards provide a quick health check — are there periods that should have been closed but aren't?
- **Locking:** After the approver closes a period and all adjustments are complete, the admin locks it. Locking is the permanent seal — it prevents the approver from reopening the period. Only lock when you are certain no further adjustments will be needed. Unlocking requires admin intervention and should be rare (audit corrections only).
- **Drift correction:** The calendar runs a fixed 52-week (364-day) year anchored to Sunday–Saturday, ignoring leap days; drift accumulates ~1.25 days/year until a full week of misalignment triggers a single 53rd-period insertion to resync (~every 5–7 years).
 
**Typical workflow:**
1. Navigate to this page in December/January
2. Set the fiscal year to the upcoming year
3. Click "Generate fiscal year" — creates all periods
4. Verify the period table shows correct dates and quarter assignments
5. Throughout the year, monitor period status via summary cards
6. After the approver closes a period and all reporting is complete, lock it
 
**Period lifecycle:**
- **Open** (status 1) → Journals can be created and posted. Only the approver can close.
- **Closed** (status 2) → No new journals. Approver can reopen if adjustments are needed. Admin can lock.
- **Locked** (status 3) → Permanent. Cannot be reopened by the approver. Admin can unlock (rare, audit-only).
 
### Page Layout
 
Year selector input with generate button (disabled if the year already has periods). Summary cards per fiscal year showing open/closed/locked counts. Accordion per year expanding to a period detail table.
 
Period table columns: Period #, Name, Start Date, End Date, Days, Quarter, Closing Week flag, Status (with closed-by/locked-by attribution), Actions (Lock/Unlock).
 
### Functions
 
#### `readPeriods`
 
- **Request:** none
- **Response:** `ReadPeriodList1` — `{ elements: ReadPeriodElement1[] }`
- `ReadPeriodElement1` — `{ guid: string | null, year: int, period_number: int, period_name: string, start_date: string, end_date: string, days_in_period: int | null, quarter_number: int | null, has_closing_week: bool, is_leap_adjustment: bool, close_type: int, status: int, closed_by: string | null, closed_on: string | null, locked_by: string | null, locked_on: string | null }`
 
#### `readPeriodStatus`
 
- **Request:** `ReadPeriodStatusParams1` — `{ fiscal_year: int | null }`
- **Response:** `ReadPeriodStatusList1` — `{ elements: ReadPeriodStatusElement1[] }`
- `ReadPeriodStatusElement1` — `{ period_guid: string, fiscal_year: int, period_number: int, period_name: string, start_date: string, end_date: string, close_type: int, period_status: int, has_closing_week: bool, closed_by: string | null, closed_on: string | null, locked_by: string | null, locked_on: string | null, total_journals: int, draft_journals: int, pending_approval_journals: int, posted_journals: int, reversed_journals: int }`
 
*From `finance:reporting`. Provides journal counts per period for the summary dashboard. Pass `fiscal_year: null` for all years.*
 
#### `generateCalendar`
 
- **Request:** `GenerateCalendarParams1` — `{ fiscal_year: int, start_date: string | null }`
- **Response:** `GenerateCalendarResult1` — `{ periods: ReadPeriodElement1[] }`
 
*Creates 12 standard 28-day periods and 4 closing weeks using the 4-4-5 fiscal pattern. `start_date` is optional — defaults to the fiscal year's first day based on the configured fiscal year start.*
 
#### `lockPeriod`
 
- **Request:** `LockPeriodParams1` — `{ guid: string }`
- **Response:** `LockPeriodResult1` — `{ guid: string }`
 
*Locks a closed period. Only works on status 2 (Closed) periods. Sets status to 3 (Locked) and stamps `locked_by` / `locked_on`.*
 
#### `unlockPeriod`
 
- **Request:** `UnlockPeriodParams1` — `{ guid: string }`
- **Response:** `UnlockPeriodResult1` — `{ guid: string }`
 
*Unlocks a locked period back to Closed status. Rare — audit correction scenarios only.*
 
### Notes
 
- Period close (`closePeriod`) and reopen (`reopenPeriod`) are approver actions on the Period Management page, not admin actions. The admin only controls lock/unlock.
- The generate button is disabled if periods already exist for the selected year — prevents accidental duplicate generation.
- Period status values: 1 = Open, 2 = Closed, 3 = Locked.
- `readPeriodStatus` returns journal counts (draft, pending, posted, reversed) per period — this is dashboard data, not used for actions on this page.
 
### Description
 
Fiscal calendar management page. Generate fiscal years using the 4-4-5 pattern. Summary cards show open/closed/locked period counts per year. Accordion per year with period detail table showing dates, quarter, closing week flag, status with attribution, and lock/unlock controls. Period close is an approver action — admin controls the permanent lock. Requires `ROLE_FINANCE_ADMIN`.
 