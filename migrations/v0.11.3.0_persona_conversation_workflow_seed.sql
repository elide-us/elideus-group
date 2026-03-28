SET NOCOUNT ON;
GO

MERGE dbo.system_workflows AS target
USING (
  SELECT
    CAST('A1B2C3D4-E5F6-7890-ABCD-EF1234567890' AS UNIQUEIDENTIFIER) AS element_guid,
    CAST('persona_conversation' AS NVARCHAR(128)) AS element_name,
    CAST('Persona conversation pipeline workflow definition for Discord and API sources.' AS NVARCHAR(1024)) AS element_description,
    CAST(1 AS INT) AS element_version,
    CAST(1 AS TINYINT) AS element_status
) AS source
ON target.element_name = source.element_name
  AND target.element_version = source.element_version
WHEN MATCHED THEN
  UPDATE SET
    target.element_guid = source.element_guid,
    target.element_description = source.element_description,
    target.element_status = source.element_status,
    target.element_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN
  INSERT (
    element_guid,
    element_name,
    element_description,
    element_version,
    element_status
  )
  VALUES (
    source.element_guid,
    source.element_name,
    source.element_description,
    source.element_version,
    source.element_status
  );
GO

MERGE dbo.system_workflow_steps AS target
USING (
  SELECT *
  FROM (VALUES
    (CAST('A1B2C3D4-E5F6-7890-ABCD-EF1234567891' AS UNIQUEIDENTIFIER), CAST('A1B2C3D4-E5F6-7890-ABCD-EF1234567890' AS UNIQUEIDENTIFIER), N'parse_input', N'Validate persona_name and message are non-empty', N'pipe', N'harmless', N'server.jobs.persona_conversation_pipeline.PersonaConversationPipelineHandler.parse_input', 1),
    (CAST('A1B2C3D4-E5F6-7890-ABCD-EF1234567892' AS UNIQUEIDENTIFIER), CAST('A1B2C3D4-E5F6-7890-ABCD-EF1234567890' AS UNIQUEIDENTIFIER), N'resolve_persona', N'Load persona definition from assistant_personas', N'pipe', N'harmless', N'server.jobs.persona_conversation_pipeline.PersonaConversationPipelineHandler.resolve_persona', 2),
    (CAST('A1B2C3D4-E5F6-7890-ABCD-EF1234567893' AS UNIQUEIDENTIFIER), CAST('A1B2C3D4-E5F6-7890-ABCD-EF1234567890' AS UNIQUEIDENTIFIER), N'gather_stored_context', N'Fetch conversation history from assistant_conversations', N'pipe', N'harmless', N'server.jobs.persona_conversation_pipeline.PersonaConversationPipelineHandler.gather_stored_context', 3),
    (CAST('A1B2C3D4-E5F6-7890-ABCD-EF1234567894' AS UNIQUEIDENTIFIER), CAST('A1B2C3D4-E5F6-7890-ABCD-EF1234567890' AS UNIQUEIDENTIFIER), N'gather_channel_context', N'Fetch live Discord channel messages (skip if non-Discord source)', N'pipe', N'harmless', N'server.jobs.persona_conversation_pipeline.PersonaConversationPipelineHandler.gather_channel_context', 4),
    (CAST('A1B2C3D4-E5F6-7890-ABCD-EF1234567895' AS UNIQUEIDENTIFIER), CAST('A1B2C3D4-E5F6-7890-ABCD-EF1234567890' AS UNIQUEIDENTIFIER), N'assemble_prompt', N'Build OpenAI prompt context from system prompt + context + user message', N'pipe', N'harmless', N'server.jobs.persona_conversation_pipeline.PersonaConversationPipelineHandler.assemble_prompt', 5),
    (CAST('A1B2C3D4-E5F6-7890-ABCD-EF1234567896' AS UNIQUEIDENTIFIER), CAST('A1B2C3D4-E5F6-7890-ABCD-EF1234567890' AS UNIQUEIDENTIFIER), N'generate_response', N'Call OpenAI API', N'pipe', N'reversible', N'server.jobs.persona_conversation_pipeline.PersonaConversationPipelineHandler.generate_response', 6),
    (CAST('A1B2C3D4-E5F6-7890-ABCD-EF1234567897' AS UNIQUEIDENTIFIER), CAST('A1B2C3D4-E5F6-7890-ABCD-EF1234567890' AS UNIQUEIDENTIFIER), N'log_and_deliver', N'Write messages to DB and deliver response to output channel', N'pipe', N'irreversible', N'server.jobs.persona_conversation_pipeline.PersonaConversationPipelineHandler.log_and_deliver', 7)
  ) AS workflow_steps (element_guid, workflows_guid, element_name, element_description, element_step_type, element_disposition, element_class_path, element_sequence)
) AS source
ON target.workflows_guid = source.workflows_guid
  AND target.element_name = source.element_name
WHEN MATCHED THEN
  UPDATE SET
    target.element_guid = source.element_guid,
    target.element_description = source.element_description,
    target.element_step_type = source.element_step_type,
    target.element_disposition = source.element_disposition,
    target.element_class_path = source.element_class_path,
    target.element_sequence = source.element_sequence,
    target.element_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN
  INSERT (
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
    source.element_guid,
    source.workflows_guid,
    source.element_name,
    source.element_description,
    source.element_step_type,
    source.element_disposition,
    source.element_class_path,
    source.element_sequence
  );
GO
