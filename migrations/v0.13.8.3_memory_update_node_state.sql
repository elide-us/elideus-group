-- ============================================================================
-- elideus-group v0.13.8.3 — repoint memory.entries.update at pub_node_state
-- Date: 2026-07-24
-- Implements: FDD-ORACLE-MEM-UNIFY-01 §A3 follow-up (REQUIRED, not optional)
--
-- WHY THIS EXISTS
--   v0.13.8.0 §A3 replaced agent_memory_entries.pub_is_active with a PERSISTED
--   computed projection of pub_node_state. That migration asserted in its
--   header that no code path writes pub_is_active. THAT ASSERTION WAS WRONG.
--
--   The registered query memory.entries.update (seeded in
--   v0.13.1.0_memory_seed.sql, key 654F7A79-F7E9-5CD9-BCF6-28C8A943953B)
--   assigns it:
--       pub_is_active = COALESCE(TRY_CAST(? AS BIT), pub_is_active)
--   inside a multi-line UPDATE. The check that cleared A3 grepped for
--   'pub_is_active' on the same line as UPDATE/SET, so a statement whose SET
--   clause spans lines was never examined. memory_update has been failing since
--   v0.13.8.0 applied, with:
--       Msg 271 — The column "pub_is_active" cannot be modified because it is
--       either a computed column or is the result of a UNION operator.
--
--   Only this one query assigns the column; a multi-line-aware sweep of every
--   migration found no others. Blast radius is this statement alone.
--
-- THE FIX
--   The is_active parameter now drives pub_node_state, and pub_is_active
--   follows automatically as its computed projection — which is what §A3
--   intended: one canonical state field, with the bit kept only so existing
--   reads and indexes keep working.
--
--   Mapping (matches the values v0.13.3.0's conflict queries already write):
--       is_active = 1     -> pub_node_state = 'active'
--       is_active = 0     -> pub_node_state = 'retired'
--       is_active IS NULL -> unchanged
--
--   The CASE is written to consume exactly ONE positional parameter:
--       COALESCE(CASE TRY_CAST(? AS BIT) WHEN 1 THEN ... WHEN 0 THEN ... END, pub_node_state)
--   With no ELSE, a NULL cast matches no WHEN and yields NULL, so COALESCE
--   falls through to the existing value. Referencing the parameter twice would
--   have changed the positional parameter count and broken every caller.
--
--   The parameter contract is therefore UNCHANGED:
--       title, body, tags, kind, is_active, key_guid, key_guid
--   No application code changes. Part C may retire the is_active parameter in
--   favour of an explicit node_state, but that is a contract change and does
--   not belong in a repair.
--
-- Idempotent (plain UPDATE of the registered query text).
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

UPDATE [dbo].[system_objects_queries]
   SET [pub_query_text] = N'SET NOCOUNT ON;
UPDATE [dbo].[agent_memory_entries]
SET pub_title       = COALESCE(?, pub_title),
    pub_body        = COALESCE(?, pub_body),
    pub_tags        = COALESCE(?, pub_tags),
    pub_kind        = COALESCE(?, pub_kind),
    pub_node_state  = COALESCE(CASE TRY_CAST(? AS BIT) WHEN 1 THEN N''active'' WHEN 0 THEN N''retired'' END, pub_node_state),
    priv_modified_on = SYSUTCDATETIME()
WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER);
SELECT key_guid
FROM [dbo].[agent_memory_entries]
WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;',
       [pub_description] = N'Patch a memory entry. COALESCE preserves existing values when a param is NULL. The is_active param drives pub_node_state (1=active, 0=retired); pub_is_active is a computed projection and cannot be written directly. Returns key_guid (empty if not found).'
 WHERE [key_guid] = N'654F7A79-F7E9-5CD9-BCF6-28C8A943953B';
GO


-- ============================================================================
-- Verification
-- ============================================================================

-- 1) The registered text no longer assigns the computed column.
SELECT N'assigns pub_is_active (expect 0)' AS [check], COUNT(*) AS [count]
  FROM [dbo].[system_objects_queries]
 WHERE [pub_name] LIKE N'memory.%'
   AND [pub_query_text] LIKE N'%pub_is_active%=%';

-- 2) The parameter contract is untouched.
SELECT N'parameter_names' AS [check], [pub_parameter_names]
  FROM [dbo].[system_objects_queries]
 WHERE [key_guid] = N'654F7A79-F7E9-5CD9-BCF6-28C8A943953B';
-- expect: title,body,tags,kind,is_active,key_guid,key_guid

-- 3) Live smoke test: round-trip a real entry through retire and reactivate,
--    asserting the computed projection tracks pub_node_state. Restores the
--    original state before finishing.
DECLARE @probe UNIQUEIDENTIFIER = (
    SELECT TOP 1 key_guid FROM [dbo].[agent_memory_entries]
     WHERE pub_node_state = N'active' ORDER BY priv_created_on DESC);
DECLARE @orig NVARCHAR(24) = (SELECT pub_node_state FROM [dbo].[agent_memory_entries] WHERE key_guid = @probe);

UPDATE [dbo].[agent_memory_entries]
   SET pub_node_state = COALESCE(CASE TRY_CAST(0 AS BIT) WHEN 1 THEN N'active' WHEN 0 THEN N'retired' END, pub_node_state)
 WHERE key_guid = @probe;
SELECT N'after retire' AS [step], pub_node_state, pub_is_active
  FROM [dbo].[agent_memory_entries] WHERE key_guid = @probe;   -- expect retired / 0

UPDATE [dbo].[agent_memory_entries]
   SET pub_node_state = COALESCE(CASE TRY_CAST(NULL AS BIT) WHEN 1 THEN N'active' WHEN 0 THEN N'retired' END, pub_node_state)
 WHERE key_guid = @probe;
SELECT N'after NULL param (must not change)' AS [step], pub_node_state, pub_is_active
  FROM [dbo].[agent_memory_entries] WHERE key_guid = @probe;   -- expect retired / 0

UPDATE [dbo].[agent_memory_entries] SET pub_node_state = @orig WHERE key_guid = @probe;
SELECT N'restored' AS [step], pub_node_state, pub_is_active
  FROM [dbo].[agent_memory_entries] WHERE key_guid = @probe;   -- expect active / 1
GO
