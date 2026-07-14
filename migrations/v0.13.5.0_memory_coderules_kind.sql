-- ============================================================================
-- elideus-group v0.13.5.0 — memory_coderules classifies on KIND, not a tag
-- Date: 2026-07-14
--
-- Correction (rule DDD070C7 "enhance the existing system; never build a
-- parallel reimplementation"): v0.13.4.0 marked rules with a NEW `rule` tag and
-- filtered memory_coderules on it — but `pub_kind` is already the system's
-- classifier, and the query already filters on it. A rule is a classification;
-- kind is the classifier; so `rule` is a KIND value, not a second parallel
-- classifier. This repoints the query at `pub_kind = 'rule'`, reusing the
-- mechanism that already exists.
--
-- Companion data change (applied via the live memory_* tools, not this file):
-- the rule entries are reclassified to kind='rule'; the now-redundant `rule`
-- tag is retired once this migration is deployed.
--
-- Idempotent single UPDATE of the registered query. Params are unchanged
-- (limit, project, project, query, query), so no module code change is needed
-- beyond docstrings. Apply BEFORE redeploying (module reloads the query at
-- startup).
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO


-- The only change from v0.13.4.0 is the classifier line:
--   was:  AND EXISTS (STRING_SPLIT(pub_tags,' ') = 'rule')     -- parallel tag classifier
--   now:  AND pub_kind = N'rule'                               -- the existing classifier
UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'SELECT TOP (?) key_guid, ref_thread_guid, pub_project, pub_kind, pub_title, pub_body,
       pub_tags, pub_source, pub_confidence, pub_confidence_source, pub_node_state, pub_ref_count,
       CAST(pub_confidence * (1 + pub_ref_count) AS DECIMAL(19,5)) AS authority,
       priv_created_on, priv_modified_on
FROM [dbo].[agent_memory_entries]
WHERE pub_is_active = 1
  AND pub_node_state = N''active''
  AND pub_kind = N''rule''
  AND (? IS NULL OR pub_project = ? OR pub_project = N''general'')
  AND (? IS NULL OR NOT EXISTS (
        SELECT 1 FROM STRING_SPLIT(?, N'' '') s
        WHERE s.value <> N''''
          AND pub_title NOT LIKE N''%'' + s.value + N''%''
          AND pub_body  NOT LIKE N''%'' + s.value + N''%''
          AND COALESCE(pub_tags, N'''') NOT LIKE N''%'' + s.value + N''%''))
ORDER BY authority DESC, priv_modified_on DESC
FOR JSON PATH, INCLUDE_NULL_VALUES;',
  [pub_description] = N'Code-rules bank (backs memory_coderules): authority-ranked (confidence*(1+ref_count)) active entries of KIND ''rule'', folding in universal ''general'' rules when a project is given; optional tokenized query. Rule is a kind (the existing classifier), not a tag.'
WHERE [pub_name] = N'memory.entries.consult';
GO


-- ============================================================================
-- Verification
-- ============================================================================

SELECT pub_name, pub_parameter_names FROM [dbo].[system_objects_queries]
WHERE pub_name = N'memory.entries.consult';

-- What the bank returns now (entries classified kind='rule')
SELECT pub_project, pub_title,
       CAST(pub_confidence * (1 + pub_ref_count) AS DECIMAL(19,5)) AS authority
FROM [dbo].[agent_memory_entries]
WHERE pub_is_active = 1 AND pub_node_state = N'active' AND pub_kind = N'rule'
ORDER BY authority DESC;
GO
