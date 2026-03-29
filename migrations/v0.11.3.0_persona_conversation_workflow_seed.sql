SET NOCOUNT ON;
GO


-- Clean up duplicate persona_conversation workflows (keep the canonical one)
DELETE FROM system_workflow_steps
WHERE workflows_guid IN (
  SELECT element_guid
  FROM system_workflows
  WHERE element_name = 'persona_conversation'
    AND element_guid != 'A1B2C3D4-E5F6-7890-ABCD-EF1234567890'
);
GO

DELETE FROM system_workflows
WHERE element_name = 'persona_conversation'
  AND element_guid != 'A1B2C3D4-E5F6-7890-ABCD-EF1234567890';
GO

IF NOT EXISTS (
  SELECT 1 FROM system_workflows
  WHERE element_name = 'persona_conversation' AND element_version = 1
)
BEGIN
  INSERT INTO system_workflows (
    element_guid,
    element_name,
    element_description,
    element_version,
    element_status
  )
  VALUES (
    'A1B2C3D4-E5F6-7890-ABCD-EF1234567890',
    'persona_conversation',
    'Persona conversation pipeline workflow definition for Discord and API sources.',
    1,
    1
  );
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM system_workflow_steps
  WHERE workflows_guid = 'A1B2C3D4-E5F6-7890-ABCD-EF1234567890' AND element_name = 'resolve_persona'
)
BEGIN
  INSERT INTO system_workflow_steps (
    element_guid,
    workflows_guid,
    element_name,
    element_description,
    element_step_type,
    element_disposition,
    element_class_path,
    element_sequence
  )
  VALUES (
    'A1B2C3D4-E5F6-7890-ABCD-EF1234567891',
    'A1B2C3D4-E5F6-7890-ABCD-EF1234567890',
    'resolve_persona',
    'Load persona definition from assistant_personas',
    'pipe',
    'harmless',
    'server.workflows.steps.conversation.ResolvePersonaStep',
    1
  );
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM system_workflow_steps
  WHERE workflows_guid = 'A1B2C3D4-E5F6-7890-ABCD-EF1234567890' AND element_name = 'gather_stored_context'
)
BEGIN
  INSERT INTO system_workflow_steps (
    element_guid,
    workflows_guid,
    element_name,
    element_description,
    element_step_type,
    element_disposition,
    element_class_path,
    element_sequence
  )
  VALUES (
    'A1B2C3D4-E5F6-7890-ABCD-EF1234567892',
    'A1B2C3D4-E5F6-7890-ABCD-EF1234567890',
    'gather_stored_context',
    'Fetch conversation history from assistant_conversations',
    'pipe',
    'harmless',
    'server.workflows.steps.conversation.GatherStoredContextStep',
    2
  );
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM system_workflow_steps
  WHERE workflows_guid = 'A1B2C3D4-E5F6-7890-ABCD-EF1234567890' AND element_name = 'assemble_prompt'
)
BEGIN
  INSERT INTO system_workflow_steps (
    element_guid,
    workflows_guid,
    element_name,
    element_description,
    element_step_type,
    element_disposition,
    element_class_path,
    element_sequence
  )
  VALUES (
    'A1B2C3D4-E5F6-7890-ABCD-EF1234567893',
    'A1B2C3D4-E5F6-7890-ABCD-EF1234567890',
    'assemble_prompt',
    'Build OpenAI prompt context from system prompt + context + user message',
    'pipe',
    'harmless',
    'server.workflows.steps.conversation.AssemblePromptStep',
    3
  );
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM system_workflow_steps
  WHERE workflows_guid = 'A1B2C3D4-E5F6-7890-ABCD-EF1234567890' AND element_name = 'generate_response'
)
BEGIN
  INSERT INTO system_workflow_steps (
    element_guid,
    workflows_guid,
    element_name,
    element_description,
    element_step_type,
    element_disposition,
    element_class_path,
    element_sequence
  )
  VALUES (
    'A1B2C3D4-E5F6-7890-ABCD-EF1234567894',
    'A1B2C3D4-E5F6-7890-ABCD-EF1234567890',
    'generate_response',
    'Call OpenAI API',
    'pipe',
    'harmless',
    'server.workflows.steps.conversation.GenerateResponseStep',
    4
  );
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM system_workflow_steps
  WHERE workflows_guid = 'A1B2C3D4-E5F6-7890-ABCD-EF1234567890' AND element_name = 'log_conversation'
)
BEGIN
  INSERT INTO system_workflow_steps (
    element_guid,
    workflows_guid,
    element_name,
    element_description,
    element_step_type,
    element_disposition,
    element_class_path,
    element_sequence
  )
  VALUES (
    'A1B2C3D4-E5F6-7890-ABCD-EF1234567895',
    'A1B2C3D4-E5F6-7890-ABCD-EF1234567890',
    'log_conversation',
    'Write messages to assistant_conversations',
    'stack',
    'reversible',
    'server.workflows.steps.conversation.LogConversationStep',
    5
  );
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM system_workflows
  WHERE element_name = 'billing_import' AND element_version = 1
)
BEGIN
  INSERT INTO system_workflows (
    element_guid,
    element_name,
    element_description,
    element_version,
    element_status
  )
  VALUES (
    'B1C2D3E4-F5A6-7890-BCDE-F12345678900',
    'billing_import',
    'Promote approved billing staging imports into posted journals.',
    1,
    1
  );
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM system_workflow_steps
  WHERE workflows_guid = 'B1C2D3E4-F5A6-7890-BCDE-F12345678900' AND element_name = 'validate_import'
)
BEGIN
  INSERT INTO system_workflow_steps (
    element_guid,
    workflows_guid,
    element_name,
    element_description,
    element_step_type,
    element_disposition,
    element_class_path,
    element_sequence
  )
  VALUES (
    'B1C2D3E4-F5A6-7890-BCDE-F12345678901',
    'B1C2D3E4-F5A6-7890-BCDE-F12345678900',
    'validate_import',
    'Validate import status and eligibility before promotion',
    'pipe',
    'harmless',
    'server.workflows.steps.billing_import.ValidateImportStep',
    1
  );
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM system_workflow_steps
  WHERE workflows_guid = 'B1C2D3E4-F5A6-7890-BCDE-F12345678900' AND element_name = 'classify_costs'
)
BEGIN
  INSERT INTO system_workflow_steps (
    element_guid,
    workflows_guid,
    element_name,
    element_description,
    element_step_type,
    element_disposition,
    element_class_path,
    element_sequence
  )
  VALUES (
    'B1C2D3E4-F5A6-7890-BCDE-F12345678902',
    'B1C2D3E4-F5A6-7890-BCDE-F12345678900',
    'classify_costs',
    'Resolve account mappings and classify staging line items',
    'pipe',
    'harmless',
    'server.workflows.steps.billing_import.ClassifyCostsStep',
    2
  );
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM system_workflow_steps
  WHERE workflows_guid = 'B1C2D3E4-F5A6-7890-BCDE-F12345678900' AND element_name = 'create_journal'
)
BEGIN
  INSERT INTO system_workflow_steps (
    element_guid,
    workflows_guid,
    element_name,
    element_description,
    element_step_type,
    element_disposition,
    element_class_path,
    element_sequence
  )
  VALUES (
    'B1C2D3E4-F5A6-7890-BCDE-F12345678903',
    'B1C2D3E4-F5A6-7890-BCDE-F12345678900',
    'create_journal',
    'Create and post the billing journal entry',
    'pipe',
    'irreversible',
    'server.workflows.steps.billing_import.CreateJournalStep',
    3
  );
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM system_workflow_steps
  WHERE workflows_guid = 'B1C2D3E4-F5A6-7890-BCDE-F12345678900' AND element_name = 'mark_promoted'
)
BEGIN
  INSERT INTO system_workflow_steps (
    element_guid,
    workflows_guid,
    element_name,
    element_description,
    element_step_type,
    element_disposition,
    element_class_path,
    element_sequence
  )
  VALUES (
    'B1C2D3E4-F5A6-7890-BCDE-F12345678904',
    'B1C2D3E4-F5A6-7890-BCDE-F12345678900',
    'mark_promoted',
    'Mark staging import as promoted after journal posting',
    'pipe',
    'irreversible',
    'server.workflows.steps.billing_import.MarkPromotedStep',
    4
  );
END;
GO
