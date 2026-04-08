## Number Sequences
 
**Route:** `/finance/approver/sequences`
 
*Manage number sequence families used for generating posting keys, lot numbers, SKUs, and other sequential identifiers across the finance module. Number sequences ensure unique, traceable, audit-friendly identifiers for all financial transactions.*
 
### Functional Activity
 
Every financial transaction needs a unique human-readable identifier — a posting key for journals, a lot number for credit lots, a SKU for products. Number sequences generate these identifiers systematically, ensuring they follow a consistent pattern, never collide, and provide a clear audit trail.
 
Each sequence is scoped to a GL account and defines a numbering family: a prefix, an allocation range, a reset policy, and a pattern. When a journal is created or a credit lot is issued, the system draws the next number from the appropriate sequence.
 
**When to use this page:**
- **Initial setup:** Create number sequences for each type of transaction — journal posting keys, credit lot numbers, product SKUs. Each sequence is bound to a GL account that contextualizes its purpose.
- **New transaction types:** When a new category of financial document is introduced, create a sequence for it. Without a sequence, the system cannot generate posting keys for that category.
- **Sequence management:** Monitor remaining capacity (max number minus last number), adjust allocation sizes for high-volume vs. low-volume sequences, and manage series rollovers.
- **Pattern configuration:** Define the display format and pattern for generated identifiers — e.g., `JNL-{NNNNNN}` for journals, `LOT-{NNNNNN}` for credit lots.
 
**Sequence concepts:**
- **Prefix:** Fixed string prepended to the number (e.g., "JNL", "LOT", "SKU")
- **Account binding:** Each sequence is scoped to a GL account — this is the contextual anchor, not a posting target
- **Allocation size:** How many numbers are pre-allocated per batch. Larger allocations reduce contention in high-concurrency scenarios but may leave gaps on restart
- **Continuous vs. non-continuous:** Continuous sequences guarantee gap-free numbering (slower, requires serialization). Non-continuous allows gaps (faster, suitable for most business use)
- **Reset policy:** When the sequence counter resets — Never, FiscalYear, or FiscalPeriod
- **Series:** When a sequence exhausts its range or rolls over on reset, the series number increments and the counter restarts
 
### Page Layout
 
Create button opens a collapsible inline form with all sequence configuration fields. Table displays all sequences with prefix, account number, scope, type, series, last number, allocation, status, pattern, remaining capacity, and edit/delete actions.
 
### Functions
 
#### `readNumberSequences`
 
- **Request:** none
- **Response:** `ReadNumberSequenceList1` — `{ elements: ReadNumberSequenceElement1[] }`
- `ReadNumberSequenceElement1` — `{ guid: string, accounts_guid: string, prefix: string | null, account_number: string, last_number: int, max_number: int | null, allocation_size: int, reset_policy: string, sequence_status: int, sequence_type: string, series_number: int, scope: string | null, pattern: string | null, display_format: string | null, account_name: string | null, remaining: int | null }`
 
*`account_name` and `remaining` are computed display fields.*
 
#### `createNumberSequence`
 
- **Request:** `CreateNumberSequenceParams1` — `{ accounts_guid: string, prefix: string | null, account_number: string, last_number: int, max_number: int | null, allocation_size: int, reset_policy: string, sequence_type: string, scope: string | null, pattern: string | null, display_format: string | null }`
- **Response:** `CreateNumberSequenceResult1` — `{ guid: string, account_number: string }`
 
*GUID is generated server-side (non-deterministic). Sequence status defaults to active, series number defaults to 1.*
 
#### `updateNumberSequence`
 
- **Request:** `UpdateNumberSequenceParams1` — `{ guid: string, prefix: string | null, max_number: int | null, allocation_size: int, reset_policy: string, sequence_status: int, pattern: string | null, display_format: string | null }`
- **Response:** `UpdateNumberSequenceResult1` — `{ guid: string, account_number: string }`
 
*Account binding, account number, sequence type, and scope are immutable after creation — these define the sequence's identity. Operational fields (prefix, max, allocation, reset policy, status, pattern, display format) are editable.*
 
#### `deleteNumberSequence`
 
- **Request:** `DeleteNumberSequenceParams1` — `{ guid: string }`
- **Response:** `DeleteNumberSequenceResult1` — `{ guid: string }`
 
#### `getNextNumber`
 
- **Request:** `GetNextNumberParams1` — `{ guid: string }`
- **Response:** `GetNextNumberResult1` — `{ guid: string, number: string }`
 
*Draws and returns the next number from the sequence. Used for testing and manual number generation.*
 
### Shared Lookups
 
- `readAccounts` — populates the parent account dropdown in the sequence form
 
### Notes
 
- Number sequences were previously duplicated across the Admin and Accountant tabs. In the realignment they live exclusively on the Approver page — number sequence configuration is a business decision, not a system infrastructure concern or a transactional activity.
- The `shift` operation (rolling over to a new series) exists in the RPC subdomain but is not yet surfaced in the UI. It would allow the manager to manually close a sequence and start a new series.
 
### Description
 
Number sequence management. Collapsible inline form for create/edit with prefix, parent account, account number, scope, sequence type, series, last/max number, allocation size, reset policy, pattern, and display format. Table shows all sequences with computed remaining capacity. Sequences generate unique identifiers for journals, credit lots, SKUs, and other financial documents. Requires `ROLE_FINANCE_APPR`.
 