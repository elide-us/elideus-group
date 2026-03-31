-- ============================================================================
-- TheOracleRPC v0.11 Automation Cleanup Migration
-- Date: 2026-03-31
-- Purpose:
--   1. Fix billing_import workflow description
--   2. Update summarize persona prompt with template fields
--   3. Seed system_workflow_actions for storage_reindex and stall_monitor
-- ============================================================================

SET XACT_ABORT ON;
BEGIN TRANSACTION;

-- ============================================================================
-- 1. Fix billing_import workflow description
-- ============================================================================

UPDATE system_workflows
SET element_description = N'Import billing data from vendor APIs to financial staging tables.',
    element_modified_on = SYSUTCDATETIME()
WHERE element_name = N'billing_import';

-- ============================================================================
-- 2. Update summarize persona prompt with template fields
-- ============================================================================

UPDATE assistant_personas
SET element_prompt = N'You provide concise summaries of conversations. You are summarizing {message_count} messages from the channel #{channel_name}.

Channel context:
{channel_messages}

Stored conversation context:
{conversation_history}

Produce a summary highlighting key decision points raised or resolved, with a social and connection highlight for conversations.',
    element_modified_on = SYSUTCDATETIME()
WHERE element_name = N'summarize';

-- ============================================================================
-- 3. Seed system_workflow_actions for storage_reindex and stall_monitor
--
--    The function GUIDs are looked up from reflection at execution time.
--    Subdomain names in reflection are just 'storage' and 'workflows'
--    (under the 'system' domain), NOT dot-notation like 'workflows.storage'.
-- ============================================================================

-- Clear any existing action rows for these workflows (idempotent)
DELETE FROM system_workflow_actions
WHERE workflows_guid IN (
  N'C1D2E3F4-A5B6-7890-CDEF-123456789010',  -- storage_reindex
  N'D1E2F3A4-B5C6-7890-DEFA-123456789020'   -- stall_monitor
);

-- storage_reindex → system.storage.get_stats (with config reindex=true)
-- The function 'get_stats' lives under subdomain 'storage' in the 'system' domain.
INSERT INTO system_workflow_actions (
  workflows_guid,
  element_name,
  element_description,
  functions_guid,
  dispositions_recid,
  element_sequence,
  element_is_optional,
  element_is_active,
  element_config,
  element_created_on,
  element_modified_on
)
SELECT
  N'C1D2E3F4-A5B6-7890-CDEF-123456789010',
  N'reindex_storage',
  N'Scan blob storage and sync users_storage_cache',
  f.element_guid,
  3,  -- idempotent
  1,
  0,
  1,
  N'{"reindex": true}',
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
FROM reflection_rpc_functions f
INNER JOIN reflection_rpc_subdomains s ON s.element_guid = f.subdomains_guid
INNER JOIN reflection_rpc_domains d ON d.element_guid = s.domains_guid
WHERE d.element_name = N'system'
  AND s.element_name = N'storage'
  AND f.element_name = N'get_stats'
  AND f.element_status = 1;

-- Verify the insert worked
IF NOT EXISTS (
  SELECT 1 FROM system_workflow_actions
  WHERE workflows_guid = N'C1D2E3F4-A5B6-7890-CDEF-123456789010'
)
BEGIN
  RAISERROR('Failed to seed storage_reindex action: function system.storage.get_stats not found in reflection', 16, 1);
  ROLLBACK TRANSACTION;
  RETURN;
END;

-- stall_monitor → system.workflows.scan_stalls
INSERT INTO system_workflow_actions (
  workflows_guid,
  element_name,
  element_description,
  functions_guid,
  dispositions_recid,
  element_sequence,
  element_is_optional,
  element_is_active,
  element_created_on,
  element_modified_on
)
SELECT
  N'D1E2F3A4-B5C6-7890-DEFA-123456789020',
  N'scan_stalled_runs',
  N'Scan for workflow runs exceeding their stall threshold and flag them',
  f.element_guid,
  3,  -- idempotent
  1,
  0,
  1,
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
FROM reflection_rpc_functions f
INNER JOIN reflection_rpc_subdomains s ON s.element_guid = f.subdomains_guid
INNER JOIN reflection_rpc_domains d ON d.element_guid = s.domains_guid
WHERE d.element_name = N'system'
  AND s.element_name = N'workflows'
  AND f.element_name = N'scan_stalls'
  AND f.element_status = 1;

-- Verify the insert worked
IF NOT EXISTS (
  SELECT 1 FROM system_workflow_actions
  WHERE workflows_guid = N'D1E2F3A4-B5C6-7890-DEFA-123456789020'
)
BEGIN
  RAISERROR('Failed to seed stall_monitor action: function system.workflows.scan_stalls not found in reflection', 16, 1);
  ROLLBACK TRANSACTION;
  RETURN;
END;

COMMIT TRANSACTION;

-- Summary output
SELECT 'workflow_actions_seeded' AS [check],
       COUNT(*) AS [count]
FROM system_workflow_actions
WHERE workflows_guid IN (
  N'C1D2E3F4-A5B6-7890-CDEF-123456789010',
  N'D1E2F3A4-B5C6-7890-DEFA-123456789020'
);

SELECT 'billing_import_description' AS [check],
       element_description AS [value]
FROM system_workflows
WHERE element_name = N'billing_import';

SELECT 'summarize_prompt_updated' AS [check],
       CASE WHEN element_prompt LIKE N'%{channel_messages}%' THEN 'YES' ELSE 'NO' END AS [value]
FROM assistant_personas
WHERE element_name = N'summarize';