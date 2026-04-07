# Existing Workflows Reference

*Documents the four workflow definitions currently registered in `system_workflows` as of the refactoring baseline. This serves as a reference for rebuild continuity and expansion under the new automation module.*

---

## 1. Storage Reindex

**Name:** `storage_reindex`
**Status:** Published, Active
**Max Concurrency:** 1
**Stall Threshold:** 3600s (1 hour)

### Purpose

Scans Azure Blob Storage and synchronizes the `users_storage_cache` table. Ensures the database index matches what's actually in blob storage.

### Actions

| Seq | Name | Disposition | Description |
|---|---|---|---|
| 1 | `reindex_storage` | Idempotent | Scan blob storage and sync `users_storage_cache`. Config: `{"reindex": true}` |

### Scheduled Task

- **Name:** Storage Reindex
- **Cron:** `0 */12 * * *` (every 12 hours)
- **Status:** Enabled

### Run History

One completed run on record (triggered via RPC, completed successfully). Result: 91 files, ~450MB, 9 folders, 6 user folders, 88 DB rows.

---

## 2. Stall Monitor

**Name:** `stall_monitor`
**Status:** Published, Active
**Max Concurrency:** 1
**Stall Threshold:** 300s (5 minutes)

### Purpose

Scans for workflow runs stuck in running or waiting status longer than their configured stall threshold. Transitions detected runs to `stalled` status for operator review or automated retry.

### Actions

| Seq | Name | Disposition | Description |
|---|---|---|---|
| 1 | `scan_stalled_runs` | Idempotent | Scan for runs exceeding stall threshold and flag them |

### Scheduled Task

- **Name:** Stall Monitor
- **Cron:** `*/5 * * * *` (every 5 minutes)
- **Status:** Enabled

### Run History

No completed runs on record.

---

## 3. Persona Conversation

**Name:** `persona_conversation`
**Status:** Published, Active
**Max Concurrency:** not set
**Stall Threshold:** 300s (5 minutes)

### Purpose

Persona conversation pipeline for Discord and API sources. Intended to orchestrate the full persona response flow: receive input, select persona, call AI model, store conversation, return response, deduct credits.

### Actions

No actions currently wired — workflow skeleton exists but pipeline stages have not been connected.

### Scheduled Task

None — this workflow is triggered on demand (via Discord bot command or RPC).

### Notes

This is the workflow that the `!persona` Discord command should submit to. The orchestrator engine exists but the action pipeline was never completed. Rebuild should wire this up with actions for: input validation, persona/model resolution, AI API call, conversation storage, credit deduction, response delivery.

---

## 4. Billing Import

**Name:** `billing_import`
**Status:** Published, Active
**Max Concurrency:** 1
**Stall Threshold:** 1800s (30 minutes)

### Purpose

Import billing data from vendor APIs into the financial staging tables. Pulls cost/usage data from cloud providers (Azure) and other vendor APIs, stages it for review and promotion into the GL journal system.

### Actions

No actions currently wired — workflow definition exists but pipeline stages have not been connected.

### Scheduled Task

None currently — intended to be scheduled (e.g. monthly or on-demand before period close).

### Notes

This workflow feeds the finance staging pipeline. The staging tables (`finance_staging_imports`, `finance_staging_line_items`, `finance_staging_azure_cost_details`, `finance_staging_azure_invoices`) exist and the manual import flow works through the finance UI. This workflow is meant to automate what is currently a manual process.

---

## Summary

| Workflow | Actions Wired | Scheduled | Operational |
|---|---|---|---|
| `storage_reindex` | Yes (1 action) | Every 12h | Yes — has completed runs |
| `stall_monitor` | Yes (1 action) | Every 5min | Yes — no runs yet |
| `persona_conversation` | No (skeleton) | No | No — pipeline not wired |
| `billing_import` | No (skeleton) | No | No — pipeline not wired |

The two operational workflows (`storage_reindex`, `stall_monitor`) are self-contained maintenance tasks. The two skeleton workflows (`persona_conversation`, `billing_import`) have definitions but no action rows — they represent planned automation that was designed but never completed.