# File Manager

**Route:** `/files`

*Personal file management interface for users with the `ENABLE_STORAGE` enablement (purchased via the Products page). Provides folder navigation, file upload, rename, move, delete, and gallery publish/unpublish controls. Backed by Azure Blob Storage with a database cache index (`users_storage_cache`).*

## Prerequisites

- User must have `ROLE_STORAGE` (grants access to the storage domain)
- Storage folder must exist — created via `createUserStorageFolder` on the User Profile page or by an admin via User Manager
- Users without storage see no route to this page; the nav entry is hidden when the enablement is absent

## Page Layout

### Upload Area

Drag-and-drop or click-to-browse file upload component at the top of the page. Uploads to the current folder path. Supports multiple files. Files are base64-encoded client-side and sent via RPC. After upload completes, the file list refreshes.

### Folder Navigation

Breadcrumb-style path display showing the current folder. Clicking a breadcrumb segment navigates to that level. A folder creation control allows creating new subfolders within the current path. Folder depth is limited to 4 levels.

### File Table

Table with three columns: Preview | Filename | Actions.

**Folders** appear first, rendered as clickable rows:
- Folder icon in preview column
- Folder name (editable inline — rename)
- Actions: "Move to" checkbox (designates this folder as the move target), Delete (disabled if non-empty)
- Clicking the row navigates into the folder
- `..` entry navigates to parent (when not at root)

**Files** follow, each row showing:
- Preview column: inline image thumbnail, audio player, video player, or open-in-new-tab icon depending on content type
- Filename column: file name (editable inline — rename), with a publish icon if the file is currently in the gallery
- Actions column: Copy Link, Delete, Publish/Unpublish (gallery toggle), Move (active when a folder is selected as move target)

### Content Type Detection

Determined from MIME type with file extension fallback:
- `audio/*` or `.mp3`, `.wav`, `.ogg` → audio preview
- `video/*` or `.mp4`, `.webm` → video preview
- `image/*` or `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.webp` → image preview
- Everything else → open-in-new-tab icon

## Table: `users_storage_cache`

| Column | Type | Notes |
|---|---|---|
| `recid` | BIGINT IDENTITY(1,1) | PK |
| `users_guid` | UNIQUEIDENTIFIER | FK → `account_users.element_guid` |
| `types_recid` | INT | FK → `storage_types.recid` |
| `element_path` | NVARCHAR(512) | Folder path (empty string for root) |
| `element_filename` | NVARCHAR(512) | File or folder name |
| `element_public` | BIT | Gallery publish flag, default `0` |
| `element_url` | NVARCHAR(2048) | Blob storage URL, nullable |
| `element_reported` | BIT | Moderation report flag, default `0` |
| `element_deleted` | BIT | Soft delete flag, default `0` |
| `moderation_recid` | BIGINT | FK → `moderation_queue.recid`, nullable |
| `element_created_on` | DATETIMEOFFSET(7) | Blob creation timestamp, nullable |
| `element_modified_on` | DATETIMEOFFSET(7) | Blob modification timestamp, nullable |

*Natural key: `(users_guid, element_path, element_filename)`. Folders are stored as rows with `content_type = 'path/folder'` (via `storage_types`). The cache is synchronized with Azure Blob Storage via the reindex workflow.*

## Lookup Table: `storage_types`

| Column | Type | Notes |
|---|---|---|
| `recid` | INT | PK |
| `element_mimetype` | NVARCHAR(128) | MIME type string |
| `element_displaytype` | NVARCHAR(64) | Human-readable type label |

*Seed includes common MIME types plus `path/folder` (recid 16) for folder entries.*

## Functions

### `readFolderContents`

- **Request:** `ReadFolderContentsParams1` — `{ path: string }`
- **Response:** `ReadFolderContentsResult1` — `{ path: string, elements: ReadFolderFileElement1[], folders: ReadFolderFolderElement1[] }`
- `ReadFolderFileElement1` — `{ path: string, name: string, url: string, content_type: string | null, gallery: bool }`
- `ReadFolderFolderElement1` — `{ name: string, empty: bool }`

*Filters to the authenticated user's files at the given path. Folders and files are separated in the response. Folder `empty` flag indicates whether delete is allowed.*

### `uploadFiles`

- **Request:** `UploadFilesParams1` — `{ files: UploadFileElement1[] }`
- `UploadFileElement1` — `{ name: string, content_b64: string, content_type: string | null }`
- **Response:** `UploadFilesResult1` — `{ files: UploadFileElement1[] }`

*Files are uploaded to the authenticated user's storage container at the path embedded in the filename. Triggers a reindex for the user after upload.*

### `deleteFiles`

- **Request:** `DeleteFilesParams1` — `{ files: string[] }`
- **Response:** `DeleteFilesResult1` — `{ files: string[] }`

*Deletes blobs from storage and removes cache rows. Each entry is a full relative path (`path/filename`). Triggers reindex.*

### `createFolder`

- **Request:** `CreateFolderParams1` — `{ path: string }`
- **Response:** `CreateFolderResult1` — `{ path: string }`

*Creates a folder marker (`.init` blob) in blob storage and upserts a `path/folder` cache row. Triggers reindex.*

### `deleteFolder`

- **Request:** `DeleteFolderParams1` — `{ path: string }`
- **Response:** `DeleteFolderResult1` — `{ path: string }`

*Deletes all blobs under the folder prefix and all corresponding cache rows. Only succeeds if the folder is empty (no files, may contain `.init`). Triggers reindex.*

### `moveFile`

- **Request:** `MoveFileParams1` — `{ src: string, dst: string }`
- **Response:** `MoveFileResult1` — `{ src: string, dst: string }`

*Copies blob to new location, deletes original. Updates cache row accordingly. Gallery flag (`element_public`) is reset to `0` on move. Triggers reindex.*

### `renameFile`

- **Request:** `RenameFileParams1` — `{ old_name: string, new_name: string }`
- **Response:** `RenameFileResult1` — `{ old_name: string, new_name: string }`

*Handles both file and folder renames. For folders, recursively renames all blobs under the old prefix. Preserves gallery flag on file rename. Triggers reindex.*

### `setGallery`

- **Request:** `SetGalleryParams1` — `{ name: string, gallery: bool }`
- **Response:** `SetGalleryResult1` — `{ name: string, gallery: bool }`

*Toggles `element_public` on the cache row. When `gallery = true`, the file appears in the public Gallery page. When `gallery = false`, the file is unpublished.*

### `getFileLink`

- **Request:** `GetFileLinkParams1` — `{ name: string }`
- **Response:** `GetFileLinkResult1` — `{ path: string, name: string, url: string }`

*Returns the blob URL for clipboard copy.*

### `getUsage`

- **Request:** none
- **Response:** `GetUsageResult1` — `{ total_size: int, by_type: GetUsageTypeElement1[] }`
- `GetUsageTypeElement1` — `{ content_type: string, size: int }`

*Returns storage consumption stats for the authenticated user. Note: `size` tracking is currently incomplete — blob sizes are not stored in the cache table. This will be addressed when the cache schema adds a `element_size` column.*

## Notes

- All file operations scope to the authenticated user's GUID — the user can only see and manipulate their own files.
- The `users_storage_cache` table is a database mirror of what's in Azure Blob Storage. The reindex workflow (`storage_reindex`) runs every 12 hours and reconciles the two. Individual file operations also trigger per-user reindex.
- Blob storage layout: `{container}/{user_guid}/{path}/{filename}`. The user GUID is the top-level partition.
- Gallery publish (`setGallery`) only affects the database flag — it does not change blob storage permissions. The gallery query reads from the cache table, not from blob storage directly.
- Move resets the gallery flag to prevent accidental exposure after reorganization.
- Folder depth is enforced at 4 levels in the current implementation.
- The File Manager page is entirely absent from the UI when the user lacks storage enablement — there is no teaser or upsell on this page itself. The Products page is where storage enablement is purchased.
- File size is not currently tracked in the cache table. Adding `element_size BIGINT` to `users_storage_cache` is a backlog item that would enable quota enforcement and accurate usage reporting.

## Description

Personal file manager at `/files` for users with storage enablement. Folder-navigable table view with upload, rename, move, delete, and gallery publish/unpublish controls. Files are stored in Azure Blob Storage and indexed in `users_storage_cache`. Content previews render inline for images, audio, and video. Gallery toggle makes files visible on the public Gallery page. All operations scope to the authenticated user's storage container.