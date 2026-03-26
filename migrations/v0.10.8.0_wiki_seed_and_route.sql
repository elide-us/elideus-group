DECLARE @author UNIQUEIDENTIFIER = '60C28D8D-96D6-4463-8962-1214E915395B';
DECLARE @wiki_id BIGINT;

IF NOT EXISTS (SELECT 1 FROM content_wiki WHERE element_slug = 'home')
BEGIN
  INSERT INTO content_wiki (
    element_slug,
    element_title,
    element_parent_slug,
    element_route_context,
    element_roles,
    element_is_active,
    element_sequence,
    element_created_by,
    element_modified_by
  )
  VALUES ('home', 'Wiki', NULL, NULL, 0, 1, 0, @author, @author);

  SET @wiki_id = SCOPE_IDENTITY();

  INSERT INTO content_wiki_versions (
    wiki_recid,
    element_version,
    element_content,
    element_edit_summary,
    element_created_by
  )
  VALUES (
    @wiki_id,
    1,
    N'Welcome to the wiki. This is the root page of the knowledge base.

## Getting Started

Browse the sub-pages below to find documentation, guides, and reference material.',
    'Initial wiki root page',
    @author
  );
END
GO

IF NOT EXISTS (SELECT 1 FROM frontend_routes WHERE element_sequence = 200)
BEGIN
  INSERT INTO frontend_routes (
    element_enablement,
    element_roles,
    element_sequence,
    element_path,
    element_name,
    element_icon
  )
  VALUES ('0', 0, 200, '/wiki/home', 'Wiki', 'MenuBook');
END
GO
