# Automation Module

**Domain:** `urn:system:automation`

*Replaces and expands the former SystemWorkflowsPage (`/system-workflows`). Subsumes `system:workflows` and `system:scheduled_tasks` RPC subdomains into a unified `system:automation` domain. This is the canonical domain for all workflow, task, and schedule management — subsuming all prior variants on task, async tasks, batch jobs, and scheduled tasks.*

---

## WorkflowCreationPage

**Route:** `/system-automation/workflows/create`

*Currently unimplemented. Future workflow designer.*

### Purpose

Visual or form-based workflow definition builder. Create new workflow definitions with ordered action steps, disposition assignments, module/method bindings, and configuration.

### Functions

#### `readWorkflowTemplate`

- **Request:** none
- **Response:** returns available modules, methods, dispositions, and trigger types for populating the builder UI

#### `createWorkflow`

- **Request:** `CreateWorkflowParams1` — `{ name: string, description: string | null, version: int, actions: CreateWorkflowActionElement1[] }`
- `CreateWorkflowActionElement1` — `{ sequence: int, name: string, disposition: string, module_attr: string, method_name: string, is_optional: bool, is_active: bool }`
- **Response:** `CreateWorkflowResult1` — `{ guid: string, name: string, version: int }`

#### `updateWorkflow`

- **Request:** `UpdateWorkflowParams1` — `{ guid: string, description: string | null, status: int, is_active: bool }`
- **Response:** `UpdateWorkflowResult1` — `{ guid: string, name: string, status: int }`

#### `deleteWorkflow`

- **Request:** `DeleteWorkflowParams1` — `{ guid: string }`
- **Response:** `DeleteWorkflowResult1` — `{ guid: string }`

---

## WorkflowManagementPage

**Route:** `/system-automation/workflows/manage`

*Partially implemented — expands the former "Runs" tab with more operational controls.*

### Purpose

Live operational dashboard for active and recent workflow runs. Monitor run status, intervene with control actions, inspect action-level detail.

### Functions

#### `readWorkflowRuns`

- **Request:** `ReadWorkflowRunsParams1` — `{ status: int | null, workflows_guid: string | null }`
- **Response:** `ReadWorkflowRunList1` — `{ elements: ReadWorkflowRunElement1[] }`
- `ReadWorkflowRunElement1` — `{ guid: string, workflows_guid: string, workflow_name: string, status: int, status_name: string, current_action: string | null, action_index: int, trigger_type: int, trigger_type_name: string, trigger_ref: string | null, payload: object | null, context: object | null, error: object | null, started_on: string | null, ended_on: string | null, created_on: string }`

#### `readWorkflowRunActions`

- **Request:** `ReadWorkflowRunActionsParams1` — `{ run_guid: string }`
- **Response:** `ReadWorkflowRunActionList1` — `{ elements: ReadWorkflowRunActionElement1[] }`
- `ReadWorkflowRunActionElement1` — `{ guid: string, actions_guid: string, action_name: string, sequence: int, status: int, status_name: string, disposition_name: string, retry_count: int, input: object | null, output: object | null, error: object | null, external_ref: string | null, started_on: string | null, ended_on: string | null }`

#### `submitWorkflowRun`

- **Request:** `SubmitWorkflowRunParams1` — `{ workflow_name: string, payload: object, trigger_type: int, trigger_ref: string | null }`
- **Response:** `SubmitWorkflowRunResult1` — `{ run_guid: string }`

#### `cancelWorkflowRun`

- **Request:** `CancelWorkflowRunParams1` — `{ guid: string }`
- **Response:** `CancelWorkflowRunResult1` — `{ guid: string, status: int }`

#### `rollbackWorkflowRun`

- **Request:** `RollbackWorkflowRunParams1` — `{ guid: string }`
- **Response:** `RollbackWorkflowRunResult1` — `{ guid: string, status: int }`

#### `resumeWorkflowRun`

- **Request:** `ResumeWorkflowRunParams1` — `{ guid: string }`
- **Response:** `ResumeWorkflowRunResult1` — `{ guid: string, status: int }`

#### `retryWorkflowRunAction`

- **Request:** `RetryWorkflowRunActionParams1` — `{ run_guid: string, action_guid: string }`
- **Response:** `RetryWorkflowRunActionResult1` — `{ run_guid: string, action_guid: string, status: int }`

#### `skipWorkflowRunAction`

- **Request:** `SkipWorkflowRunActionParams1` — `{ run_guid: string, action_guid: string }`
- **Response:** `SkipWorkflowRunActionResult1` — `{ run_guid: string, action_guid: string, status: int }`

*New — skip a failed/stalled action and advance to the next step.*

#### `gotoWorkflowRunStep`

- **Request:** `GotoWorkflowRunStepParams1` — `{ run_guid: string, target_sequence: int }`
- **Response:** `GotoWorkflowRunStepResult1` — `{ run_guid: string, action_index: int, status: int }`

*New — jump to a specific step in the workflow (for debugging or recovery).*

#### `scanStalls`

- **Request:** none
- **Response:** `ScanStallsResult1` — `{ stalled_count: int }`

*Detects runs that have been in running/waiting state longer than expected.*

---

## WorkflowHistoryPage

**Route:** `/system-automation/workflows/history`

*Follows the canonical summary + headers + detail pattern.*

### Purpose

Review completed workflow runs. Summary stats, paginated list of completed/terminal runs, drill-down to action-level logs.

### Functions

#### `readWorkflowHistorySummary`

- **Request:** none
- **Response:** `ReadWorkflowHistorySummaryResult1` — `{ total_completed: int, total_failed: int, total_cancelled: int, total_rolled_back: int }`

#### `readWorkflowHistoryHeaders`

- **Request:** `ReadWorkflowHistoryHeadersParams1` — `{ limit: int, offset: int, status: int | null }`
- **Response:** `ReadWorkflowHistoryHeaderList1` — `{ elements: ReadWorkflowRunElement1[] }`

*Reuses `ReadWorkflowRunElement1` from WorkflowManagementPage — same shape, filtered to terminal statuses.*

#### `readWorkflowHistoryDetail`

- **Request:** `ReadWorkflowHistoryDetailParams1` — `{ run_guid: string }`
- **Response:** `ReadWorkflowRunActionList1`

*Reuses `ReadWorkflowRunActionList1` from WorkflowManagementPage — same action detail shape.*

---

## TaskScheduleManagementPage

**Route:** `/system-automation/tasks/manage`

### Purpose

Create and manage scheduled task definitions. Set cron schedules, enable/disable/suspend tasks, trigger immediate execution.

### Functions

#### `readScheduledTasks`

- **Request:** none
- **Response:** `ReadScheduledTaskList1` — `{ elements: ReadScheduledTaskElement1[] }`
- `ReadScheduledTaskElement1` — `{ guid: string, name: string, description: string | null, cron_expression: string, workflow_name: string, status: int, status_name: string, last_run_on: string | null, next_run_on: string | null, created_on: string }`

#### `readScheduledTask`

- **Request:** `ReadScheduledTaskParams1` — `{ guid: string }`
- **Response:** `ReadScheduledTaskResult1` — same fields as element plus `payload: object | null`

#### `createScheduledTask`

- **Request:** `CreateScheduledTaskParams1` — `{ name: string, description: string | null, cron_expression: string, workflow_name: string, payload: object | null }`
- **Response:** `CreateScheduledTaskResult1` — `{ guid: string, name: string }`

#### `updateScheduledTask`

- **Request:** `UpdateScheduledTaskParams1` — `{ guid: string, description: string | null, cron_expression: string, status: int, payload: object | null }`
- **Response:** `UpdateScheduledTaskResult1` — `{ guid: string, status: int }`

#### `deleteScheduledTask`

- **Request:** `DeleteScheduledTaskParams1` — `{ guid: string }`
- **Response:** `DeleteScheduledTaskResult1` — `{ guid: string }`

#### `runScheduledTaskNow`

- **Request:** `RunScheduledTaskNowParams1` — `{ guid: string }`
- **Response:** `RunScheduledTaskNowResult1` — `{ guid: string, run_guid: string }`

*Immediately submits the task's workflow with trigger_type = Manual.*

---

## TaskScheduleHistoryPage

**Route:** `/system-automation/tasks/history`

*Follows the canonical summary + headers + detail pattern.*

### Purpose

Review scheduled task execution history. Summary stats, paginated list of task executions, drill-down to the associated workflow run.

### Functions

#### `readTaskHistorySummary`

- **Request:** none
- **Response:** `ReadTaskHistorySummaryResult1` — `{ total_executions: int, total_succeeded: int, total_failed: int, last_execution_on: string | null }`

#### `readTaskHistoryHeaders`

- **Request:** `ReadTaskHistoryHeadersParams1` — `{ limit: int, offset: int, task_guid: string | null }`
- **Response:** `ReadTaskHistoryHeaderList1` — `{ elements: ReadTaskHistoryHeaderElement1[] }`
- `ReadTaskHistoryHeaderElement1` — `{ recid: int, task_name: string, trigger_type_name: string, status_name: string, started_on: string, ended_on: string | null, run_guid: string | null }`

#### `readTaskHistoryDetail`

- **Request:** `ReadTaskHistoryDetailParams1` — `{ recid: int }`
- **Response:** `ReadTaskHistoryDetailResult1` — `{ recid: int, task_name: string, task_guid: string, trigger_type_name: string, status_name: string, payload: object | null, result: object | null, error: object | null, started_on: string, ended_on: string | null, run_guid: string | null }`

*`run_guid` links to the workflow run for cross-reference with WorkflowHistoryPage.*

---

## Enumerations Referenced

These lookup tables are shared across the automation domain:

- **`system_automation_statuses`** — Pending, Running, Completed, Failed, Cancelled, Waiting, Paused, Rolling Back, Rolled Back, Rollback Failed, Stalled
- **`system_trigger_types`** — Manual, Schedule, RPC, MCP, Discord, Workflow, Webhook, Poll
- **`system_dispositions`** — Pure, Reversible, Irreversible, Idempotent
- **`system_scheduled_task_statuses`** — Disabled, Enabled, Suspended

## Notes

- All five pages fall under `urn:system:automation` — a single RPC domain replacing `system:workflows` and `system:scheduled_tasks`.
- History pages follow the canonical summary + headers + detail pattern established by the Conversations page.
- WorkflowManagementPage auto-refreshes when active runs exist (poll interval TBD).
- `skipWorkflowRunAction` and `gotoWorkflowRunStep` are new operations not in the current RPC surface — they expand the operational control set.
- WorkflowCreationPage is entirely new — no current implementation exists.
- History pages are read-only with drill-down. Management pages are operational with control actions.
- Task history links back to workflow runs via `run_guid` for cross-page navigation.
- Status and disposition names are denormalized display fields resolved from lookup table joins.

## Description

Unified automation module covering workflow design, execution management, execution history, scheduled task management, and task execution history. Five pages under `/system-automation/` replace the former single-tab SystemWorkflowsPage and expand the operational surface significantly. Subsumes all prior task/workflow/schedule RPC subdomains into `urn:system:automation`.