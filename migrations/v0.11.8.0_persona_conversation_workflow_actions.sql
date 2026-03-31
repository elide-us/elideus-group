-- ==========================================================================
-- TheOracleRPC v0.11 Persona Conversation Workflow Actions
-- Date: 2026-03-31
-- Purpose:
--   1. Register workflow action callables in reflection_rpc_functions
--   2. Seed persona_conversation actions in system_workflow_actions
-- ============================================================================

SET XACT_ABORT ON;
BEGIN TRANSACTION;

DECLARE @workflow_guid UNIQUEIDENTIFIER = 'A1B2C3D4-E5F6-7890-ABCD-EF1234567890';
DECLARE @system_workflows_subdomain_guid UNIQUEIDENTIFIER;

SELECT @system_workflows_subdomain_guid = s.element_guid
FROM dbo.reflection_rpc_subdomains s
INNER JOIN dbo.reflection_rpc_domains d ON d.element_guid = s.domains_guid
WHERE d.element_name = N'system'
  AND s.element_name = N'workflows';

IF @system_workflows_subdomain_guid IS NULL
BEGIN
  RAISERROR('Missing reflection subdomain: system.workflows', 16, 1);
  ROLLBACK TRANSACTION;
  RETURN;
END;

-- --------------------------------------------------------------------------
-- 1. Reflection callables for persona workflow actions
-- --------------------------------------------------------------------------

DELETE FROM dbo.reflection_rpc_functions
WHERE element_guid IN (
  'F6DA6EE8-9145-5157-9E37-C34F250B6A01',
  '317447C0-C736-59C9-A6D5-32A3A85D0502',
  'D01D20E9-2675-5818-A4F6-95780D7E2503',
  '82AAE03D-6F74-55E8-B75A-7A6C3051BD04',
  '48991A68-C2E0-59DE-B04E-EF4A26C67605',
  'D62B7C6B-1967-5D28-94ED-CA83A9B9A306'
);

INSERT INTO dbo.reflection_rpc_functions (
  element_guid,
  subdomains_guid,
  element_name,
  element_version,
  element_module_attr,
  element_method_name,
  element_request_model_guid,
  element_response_model_guid,
  element_status,
  element_app_version,
  element_iteration,
  element_created_on,
  element_modified_on
)
VALUES
(
  'F6DA6EE8-9145-5157-9E37-C34F250B6A01',
  @system_workflows_subdomain_guid,
  N'wf_persona_conversation_resolve_persona',
  1,
  N'discord_chat',
  N'action_resolve_persona',
  NULL,
  NULL,
  1,
  NULL,
  1,
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
),
(
  '317447C0-C736-59C9-A6D5-32A3A85D0502',
  @system_workflows_subdomain_guid,
  N'wf_persona_conversation_gather_stored_context',
  1,
  N'openai',
  N'action_gather_stored_context',
  NULL,
  NULL,
  1,
  NULL,
  1,
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
),
(
  'D01D20E9-2675-5818-A4F6-95780D7E2503',
  @system_workflows_subdomain_guid,
  N'wf_persona_conversation_gather_channel_history',
  1,
  N'discord_chat',
  N'action_gather_channel_history',
  NULL,
  NULL,
  1,
  NULL,
  1,
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
),
(
  '82AAE03D-6F74-55E8-B75A-7A6C3051BD04',
  @system_workflows_subdomain_guid,
  N'wf_persona_conversation_generate_response',
  1,
  N'openai',
  N'action_generate_response',
  NULL,
  NULL,
  1,
  NULL,
  1,
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
),
(
  '48991A68-C2E0-59DE-B04E-EF4A26C67605',
  @system_workflows_subdomain_guid,
  N'wf_persona_conversation_deliver_discord',
  1,
  N'discord_chat',
  N'action_deliver_discord',
  NULL,
  NULL,
  1,
  NULL,
  1,
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
),
(
  'D62B7C6B-1967-5D28-94ED-CA83A9B9A306',
  @system_workflows_subdomain_guid,
  N'wf_persona_conversation_deliver_bsky',
  1,
  N'bsky',
  N'action_deliver_bsky',
  NULL,
  NULL,
  1,
  NULL,
  1,
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
);

-- --------------------------------------------------------------------------
-- 2. Persona workflow action definitions
-- --------------------------------------------------------------------------

DELETE FROM dbo.system_workflow_actions
WHERE workflows_guid = @workflow_guid;

INSERT INTO dbo.system_workflow_actions (
  element_guid,
  workflows_guid,
  element_name,
  element_description,
  functions_guid,
  dispositions_recid,
  element_sequence,
  element_is_optional,
  element_is_active,
  element_config,
  element_rollback_functions_guid,
  element_created_on,
  element_modified_on
)
VALUES
(
  '72E8B561-2A57-4A2D-9464-379BC7CB7001',
  @workflow_guid,
  N'resolve_persona',
  N'Resolve persona definition from payload.persona.',
  'F6DA6EE8-9145-5157-9E37-C34F250B6A01',
  0,
  1,
  0,
  1,
  NULL,
  NULL,
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
),
(
  'C1E66F1A-3375-4A83-A001-594974C47002',
  @workflow_guid,
  N'gather_stored_context',
  N'Load stored conversation and channel context for persona execution.',
  '317447C0-C736-59C9-A6D5-32A3A85D0502',
  0,
  2,
  0,
  1,
  NULL,
  NULL,
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
),
(
  'E28E1F73-FD8A-4C0E-A706-C6F77F647003',
  @workflow_guid,
  N'gather_channel_history',
  N'Fetch live Discord channel history when available.',
  'D01D20E9-2675-5818-A4F6-95780D7E2503',
  0,
  3,
  1,
  1,
  NULL,
  NULL,
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
),
(
  '36A563A4-628D-4C8D-9A74-671AA5EC7004',
  @workflow_guid,
  N'generate_response',
  N'Build prompt context, generate assistant response, and log conversation.',
  '82AAE03D-6F74-55E8-B75A-7A6C3051BD04',
  2,
  4,
  0,
  1,
  NULL,
  NULL,
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
),
(
  '45EA8EBF-9F61-4B15-997D-95967BB27005',
  @workflow_guid,
  N'deliver_discord',
  N'Queue response delivery to Discord channel.',
  '48991A68-C2E0-59DE-B04E-EF4A26C67605',
  2,
  5,
  1,
  1,
  NULL,
  NULL,
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
),
(
  'AB3D947D-EA6A-4DDA-8F73-E09421157006',
  @workflow_guid,
  N'deliver_bsky',
  N'Post generated response to Bluesky when requested.',
  'D62B7C6B-1967-5D28-94ED-CA83A9B9A306',
  2,
  6,
  1,
  1,
  NULL,
  NULL,
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
);

IF NOT EXISTS (
  SELECT 1
  FROM dbo.system_workflow_actions
  WHERE workflows_guid = @workflow_guid
)
BEGIN
  RAISERROR('Failed to seed workflow actions for persona_conversation', 16, 1);
  ROLLBACK TRANSACTION;
  RETURN;
END;

COMMIT TRANSACTION;
GO
