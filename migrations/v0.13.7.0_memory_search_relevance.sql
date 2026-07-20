-- ============================================================================
-- elideus-group v0.13.7.0 — memory_search relevance ranking (OR, not AND)
-- Date: 2026-07-20
--
-- Problem: memory.entries.search tokenised the query and required EVERY
--   whitespace term to match (AND). Multi-word queries therefore returned
--   NOTHING unless a single entry contained all terms — the #1 usability
--   complaint, and why callers fall back to memory_get.
--
-- Fix: OR-with-relevance. An entry matches if ANY term hits title/body/tags,
--   and results are ORDERED by how many DISTINCT terms match (most relevant
--   first). A query-less browse (query NULL/empty) still orders by recency.
--   A per-row match_count is surfaced for transparency.
--
-- Param list shrinks 10 -> 7 (query,project,kind,tags,tags_like,offset,limit) via
--   DECLARE-from-? — so server/modules/memory_module.py search_memory passes 7
--   params now. MemoryModule reloads queries at startup, so APPLY THIS MIGRATION
--   BEFORE redeploying the code (old code=10 params vs new query=7, or new
--   code vs old query, both break memory_search). Idempotent UPDATE.
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'DECLARE @query NVARCHAR(MAX)  = ?;
DECLARE @project NVARCHAR(128) = ?;
DECLARE @kind NVARCHAR(32)     = ?;
DECLARE @tags NVARCHAR(512)    = ?;
DECLARE @tags_like NVARCHAR(512) = ?;
DECLARE @offset INT = ?;
DECLARE @limit INT  = ?;
SELECT e.key_guid, e.ref_thread_guid, e.pub_project, e.pub_kind, e.pub_title, e.pub_body,
       e.pub_tags, e.pub_source, e.pub_confidence, e.pub_confidence_source, e.pub_node_state, e.pub_ref_count,
       e.pub_is_active, e.priv_created_on, e.priv_modified_on,
       m.match_count,
       COUNT(*) OVER() AS total
FROM [dbo].[agent_memory_entries] e
CROSS APPLY (
  SELECT COUNT(DISTINCT LTRIM(RTRIM(s.value))) AS match_count
  FROM STRING_SPLIT(COALESCE(@query, N''''), N'' '') s
  WHERE LTRIM(RTRIM(s.value)) <> N''''
    AND (e.pub_title LIKE N''%'' + s.value + N''%''
         OR e.pub_body LIKE N''%'' + s.value + N''%''
         OR COALESCE(e.pub_tags, N'''') LIKE N''%'' + s.value + N''%'')
) m
WHERE e.pub_is_active = 1
  AND (@query IS NULL OR LTRIM(RTRIM(@query)) = N'''' OR m.match_count > 0)
  AND (@project IS NULL OR e.pub_project = @project)
  AND (@kind IS NULL OR e.pub_kind = @kind)
  AND (@tags IS NULL OR e.pub_tags LIKE @tags_like)
ORDER BY CASE WHEN @query IS NULL OR LTRIM(RTRIM(@query)) = N'''' THEN 0 ELSE m.match_count END DESC,
         e.priv_modified_on DESC
OFFSET @offset ROWS FETCH NEXT @limit ROWS ONLY
FOR JSON PATH, INCLUDE_NULL_VALUES;',
  [pub_parameter_names] = N'query,project,kind,tags,tags_like,offset,limit'
WHERE [pub_name] = N'memory.entries.search';
GO

-- ============================================================================
-- Verification
-- ============================================================================
SELECT pub_name, pub_parameter_names
FROM system_objects_queries WHERE pub_name = N'memory.entries.search';   -- expect 7 params
