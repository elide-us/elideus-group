## Journals & Credits
 
**Route:** `/finance/accountant/journals`
 
*View, create, submit, and reverse journal entries. Manage credit lots. The journal is the core transactional artifact — every financial event is recorded as a balanced set of debit and credit lines posting to GL accounts. Credit lots track the credit economy — balances, grants, consumption, and expiration.*
 
### Functional Activity
 
This page is the accountant's transactional workspace. In practice, most journal creation is automated through the billing import promote pipeline, and credit lot creation is automated through the purchase flow. The accountant uses this page primarily for:
 
**Manual journal entry** — Recording transactions that don't originate from an automated pipeline. The most common scenarios:
- **Historical setup:** When first implementing the finance module, enter opening balances and historical transactions to establish the GL baseline.
- **Owner equity adjustments:** When the owner pays business expenses out of pocket (non-treasury banking), record the expense and the offsetting equity contribution.
- **Accruals and reclassifications:** End-of-period adjusting entries that don't correspond to a vendor invoice or billing import.
- **Corrections:** When a posted journal has an error that can't be reversed cleanly, create a correcting entry.
 
**Journal lifecycle management** — Reviewing generated journals from the promote pipeline, submitting them for approval, and reversing posted journals when corrections are needed.
 
**Credit lot management** — Viewing credit balances by user, granting credits (promotional grants, compensation for service issues), viewing lot event history (consumption, grants, expirations), and manually expiring lots.
 
**Journal lifecycle:**
- **Draft (0)** → Editable. Lines can be added, modified, removed.
- **Pending (1)** → Submitted for manager approval. Read-only.
- **Posted (2)** → Approved and posted to the GL. Can be reversed.
- **Reversed (3)** → A reversal journal was created. The original's effect is canceled in the GL.
 
**Double-entry rule:** Every journal must balance — total debits must equal total credits across all lines. The system enforces this on submission. Each line posts either a debit or a credit (not both) to a single GL account.
 
**When to use this page:**
- **Reviewing promoted journals:** After promoting a billing import, the generated journal appears here in Draft status. Review the lines, verify account assignments, then submit for approval.
- **Manual entry:** Create journals for transactions outside the automated pipelines — equity adjustments, accruals, historical entries, corrections.
- **Submitting for approval:** Once a journal is reviewed and correct, submit it. It appears on the manager's Approvals Workbench.
- **Reversals:** When a posted journal contains an error, reverse it. This creates a new journal with inverted debits/credits. Both journals remain in the GL — the reversal cancels the original's net effect.
- **Credit lot administration:** Grant credits to users, review lot event history, expire lots that should no longer be active.
 
### Page Layout
 
Two sections:
 
**Journals section:** Filters (fiscal year, period, status). Journal table showing posting key, name, source type, period, status, line count, total debit, total credit, and actions. Clicking a journal opens a detail view showing header metadata and lines table. Create button opens a journal creation form with header fields (name, description, source type, period, ledger) and a dynamic line editor (account dropdown, debit, credit, description, dimension picker per line). Actions: Submit for Approval (Draft), Reverse (Posted).
 
**Credit Lots section:** User GUID filter. Credit lot table showing lot number, user, source type, original credits, remaining credits, unit price, total paid, status (active/expired), event count. Clicking a lot opens an event history showing event type, credits, unit price, description, actor, and linked journal. Grant Credits button opens a creation form. Expire button on active lots.
 
### Functions — Journals
 
#### `readJournals`
 
- **Request:** `ReadJournalsParams1` — `{ journal_status: int | null, fiscal_year: int | null, periods_guid: string | null }`
- **Response:** `ReadJournalList1` — `{ elements: ReadJournalElement1[] }`
- `ReadJournalElement1` — `{ recid: int, name: string, description: string | null, posting_key: string | null, source_type: string | null, period_name: string | null, status: int, status_name: string, line_count: int, total_debit: string, total_credit: string, posted_by: string | null, posted_on: string | null, reversal_of: int | null, reversed_by: int | null, created_on: string }`
 
*`reversal_of` links a reversal journal to the original it reverses. `reversed_by` on the original points to its reversal.*
 
#### `readJournalLines`
 
- **Request:** `ReadJournalLinesParams1` — `{ journals_recid: int }`
- **Response:** `ReadJournalLineList1` — `{ elements: ReadJournalLineElement1[] }`
- `ReadJournalLineElement1` — `{ recid: int, line_number: int, account_number: string, account_name: string, debit: string, credit: string, description: string | null, dimensions: string[] }`
 
*Account number, account name, and dimension names are denormalized display fields.*
 
#### `createJournal`
 
- **Request:** `CreateJournalParams1` — `{ name: string, description: string | null, source_type: string | null, source_id: string | null, periods_guid: string | null, ledgers_recid: int | null, lines: CreateJournalLineElement1[] }`
- `CreateJournalLineElement1` — `{ line_number: int, accounts_guid: string, debit: string, credit: string, description: string | null, dimension_recids: int[] }`
- **Response:** `CreateJournalResult1` — `{ recid: int, posting_key: string }`
 
*Creates in Draft status. Posting key is auto-generated from the appropriate number sequence. The journal must contain at least one line and total debits must equal total credits.*
 
#### `submitJournal`
 
- **Request:** `SubmitJournalParams1` — `{ recid: int }`
- **Response:** `SubmitJournalResult1` — `{ recid: int, status: int }`
 
*Moves from Draft to Pending. Server-side validation confirms balance before accepting submission.*
 
#### `reverseJournal`
 
- **Request:** `ReverseJournalParams1` — `{ recid: int }`
- **Response:** `ReverseJournalResult1` — `{ recid: int, reversal_recid: int }`
 
*Creates a new journal with the same lines but debits and credits swapped. The original is marked Reversed. The reversal journal is created in Posted status — reversals don't go through the approval cycle because the original was already approved. The reversal is a corrective action that creates an auditable counter-entry rather than modifying the original. Both the original and reversal reference each other.*
 
### Functions — Credit Lots
 
#### `readCreditLotSummary`
 
- **Request:** `ReadCreditLotSummaryParams1` — `{ users_guid: string | null }`
- **Response:** `ReadCreditLotSummaryList1` — `{ elements: ReadCreditLotSummaryElement1[] }`
- `ReadCreditLotSummaryElement1` — `{ recid: int, lot_number: string, users_guid: string, source_type: string, credits_original: int, credits_remaining: int, unit_price: string, total_paid: string, expired: bool, event_count: int, created_on: string }`
 
*Pass `users_guid: null` for all lots across all users.*
 
#### `readCreditLotEvents`
 
- **Request:** `ReadCreditLotEventsParams1` — `{ lots_recid: int }`
- **Response:** `ReadCreditLotEventList1` — `{ elements: ReadCreditLotEventElement1[] }`
- `ReadCreditLotEventElement1` — `{ recid: int, event_type: string, credits: int, unit_price: string, description: string | null, actor_guid: string | null, journals_recid: int | null }`
 
*Event types: grant, consume, expire, refund. `journals_recid` links consumption and grant events to their corresponding GL journal entries.*
 
#### `createCreditLot`
 
- **Request:** `CreateCreditLotParams1` — `{ users_guid: string, source_type: string, credits: int, total_paid: string, currency: string, expires_at: string | null, source_id: string | null }`
- **Response:** `CreateCreditLotResult1` — `{ recid: int, lot_number: string }`
 
*Creates a new credit lot for a user. Lot number is auto-generated from the credit lot number sequence. Used for promotional grants, compensation grants, and manual credit issuance. Automated purchase-triggered lot creation happens through the purchase pipeline, not this function.*
 
#### `expireCreditLot`
 
- **Request:** `ExpireCreditLotParams1` — `{ recid: int }`
- **Response:** `ExpireCreditLotResult1` — `{ recid: int, expired: bool }`
 
*Marks a lot as expired. Remaining credits are zeroed. An expiration event is recorded in the lot's event history. Cannot expire an already-expired lot.*
 
#### `readWalletBalance`
 
- **Request:** `ReadWalletBalanceParams1` — `{ users_guid: string }`
- **Response:** `ReadWalletBalanceResult1` — `{ users_guid: string, balance: int }`
 
*Returns the aggregate credit balance across all active (non-expired) lots for a user. Convenience function for quick balance checks without loading full lot details.*
 
### Shared Lookups
 
- `readAccounts` — populates the account dropdown in the journal line editor (filtered to posting accounts)
- `readPeriods` — populates the period dropdown in the journal creation form (filtered to open periods)
- `readLedgers` — populates the ledger dropdown in the journal creation form
- `readDimensions` — populates the dimension picker in the journal line editor
 
### Notes
 
- Credit lots use recid as primary key because they are sequential transaction records — lot numbers are generated from number sequences and are the human-readable identifier, while recid provides sequential integrity.
- Credit lot events are also recid-keyed — they are append-only transaction records that form the audit trail for each lot.
- Journal lines reference accounts by GUID (non-deterministic) and dimensions by recid (small reference data). Master data entities use GUIDs, reference/tag data uses recids.
- The reversal workflow bypasses the approval cycle because the original journal was already approved. The reversal creates an auditable counter-entry rather than deleting or modifying the original.
- Most day-to-day accountant activity on this page is reviewing and submitting journals generated by the promote pipeline, not manual entry. The manual entry capability exists for edge cases — historical setup, equity adjustments, corrections — that don't flow through automation.
 
### Description
 
Journals and credit lot management page. Journals section: filterable journal table with detail view, creation form with dynamic line editor, submit for approval and reverse actions. Credit lots section: user-filterable lot table with event history drill-down, grant credits form, and expire action. The accountant's transactional workspace for all GL entries and credit economy management. Most journal creation is automated — manual entry is for historical setup, equity adjustments, and corrections. Requires `ROLE_FINANCE_ACCT`.