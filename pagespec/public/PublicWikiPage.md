# Wiki

**Route:** `/wiki/*` (catch-all)

*MediaWiki-style versioned wiki with hierarchical page structure, create-on-navigate, and inline editing. Public read, authenticated write.*

## Page Form

The wiki page operates in two modes with a collapsible version history footer:

### View Mode (default)

- Page title and last-modified date
- Rendered markdown content (`ReactMarkdown`)
- Sub-pages list — links to child wiki pages (pages whose `parent_slug` matches the current page slug)
- Edit button (visible only if user has `can_edit` permission)
- Version History toggle button (expands footer)

### Edit Mode

- `MarkdownEditor` component (split-pane: raw markdown left, preview right)
- Edit summary text field (optional)
- Save / Cancel buttons
- Saving creates a new version (does not overwrite — all versions are retained)

### Create-on-Navigate

When a wiki slug resolves to a 404 and the user is authenticated:
- Offers a "Create this page" prompt with the slug displayed
- Create form: page title (auto-derived from slug), `MarkdownEditor`, edit summary
- Parent slug is automatically derived from path hierarchy (e.g. `a/b/c` → parent `a/b`)
- Default title is derived from the last slug segment, hyphen-split and title-cased

### Version History Footer

Collapsible table at the bottom of view mode:
- Columns: Version # | Date | Summary | Actions
- Restore button per version (creates a new version with the restored content and summary "Restored from version N")
- Current version has no restore action

## Tables

### `content_wiki`

| Column | Type | Notes |
|---|---|---|
| `recid` | BIGINT IDENTITY(1,1) | PK |
| `element_guid` | UNIQUEIDENTIFIER | Unique, default `newid()` |
| `element_slug` | NVARCHAR(512) | URL slug, unique |
| `element_title` | NVARCHAR(512) | Page title |
| `element_parent_slug` | NVARCHAR(512) | Parent page slug, nullable (hierarchy) |
| `element_route_context` | NVARCHAR(256) | Route context, nullable |
| `element_roles` | BIGINT | Role bitmask for access control (will change with role revamp) |
| `element_is_active` | BIT | Active flag, default `1` |
| `element_sequence` | INT | Display ordering within siblings, default `0` |
| `element_created_by` | UNIQUEIDENTIFIER | FK → `account_users.element_guid` |
| `element_modified_by` | UNIQUEIDENTIFIER | FK → `account_users.element_guid` |
| `element_created_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |
| `element_modified_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |

### `content_wiki_versions`

| Column | Type | Notes |
|---|---|---|
| `recid` | BIGINT IDENTITY(1,1) | PK |
| `wiki_recid` | BIGINT | FK → `content_wiki.recid` |
| `element_version` | INT | Version number, auto-incremented per page, default `1` |
| `element_content` | NVARCHAR(MAX) | Markdown content for this version |
| `element_edit_summary` | NVARCHAR(512) | Edit summary, nullable |
| `element_created_by` | UNIQUEIDENTIFIER | FK → `account_users.element_guid` |
| `element_created_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |

*Unique constraint on `(wiki_recid, element_version)` — each page has exactly one row per version number.*

## Functions

### `readWikiPage` (public)

- **Request:** `ReadWikiPageParams1` — `{ slug: string }`
- **Response:** `ReadWikiPageResult1` — `{ slug: string, title: string, content: string | null, version: int, permissions: { can_edit: bool }, children: ReadWikiChildElement1[], element_modified_on: string | null }`
- `ReadWikiChildElement1` — `{ slug: string, title: string }`

*Returns the latest version's content. Children are pages whose `parent_slug` matches this page's slug. Permissions are computed server-side based on the requesting user's roles.*

### `createWikiPage` (authenticated)

- **Request:** `CreateWikiPageParams1` — `{ slug: string, title: string, content: string, parent_slug: string | null, edit_summary: string | null }`
- **Response:** `CreateWikiPageResult1` — `{ slug: string, title: string, version: int }`

*Creates both the `content_wiki` row and the initial `content_wiki_versions` row (version 1).*

### `createWikiVersion` (authenticated)

- **Request:** `CreateWikiVersionParams1` — `{ slug: string, content: string, edit_summary: string | null }`
- **Response:** `CreateWikiVersionResult1` — `{ slug: string, version: int }`

*Appends a new version. Does not overwrite previous versions.*

### `readWikiVersions` (authenticated)

- **Request:** `ReadWikiVersionsParams1` — `{ slug: string }`
- **Response:** `ReadWikiVersionList1` — `{ elements: ReadWikiVersionElement1[] }`
- `ReadWikiVersionElement1` — `{ recid: int, version: int, edit_summary: string | null, created_on: string }`

### `readWikiVersion` (authenticated)

- **Request:** `ReadWikiVersionParams1` — `{ slug: string, version: int }`
- **Response:** `ReadWikiVersionResult1` — `{ version: int, content: string, edit_summary: string | null, created_on: string }`

*Used by the restore flow — fetch a specific version's content, then pass it to `createWikiVersion` as a new version.*

## Slug Resolution

- Route `/wiki` or `/wiki/` resolves to slug `home`
- Route `/wiki/some/nested/path` resolves to slug `some/nested/path`
- Parent slug for `some/nested/path` is `some/nested`
- Default title for `some/nested/path` is `Path` (last segment, hyphen-split, title-cased)

## Notes

- The wiki is fully functional and self-contained — this spec documents existing behavior for rebuild continuity.
- Content is standard markdown rendered with `ReactMarkdown`.
- The `MarkdownEditor` component is shared with the Content Pages system.
- `element_roles` bitmask controls who can view/edit — this will change with the role system revamp but the functional behavior (server-computed `can_edit` permission) remains the same.
- Versions are append-only. Restore is implemented as "create a new version with old content" — no destructive operations on version history.

## Description

MediaWiki-style wiki at `/wiki/*`. View mode renders markdown with sub-page navigation. Edit mode provides a split-pane markdown editor with edit summaries. Pages are created on navigate (authenticated users visiting a non-existent slug). Version history footer shows all edits with restore capability. Hierarchical page structure via parent slug relationships. Public read, authenticated write with role-based permissions.