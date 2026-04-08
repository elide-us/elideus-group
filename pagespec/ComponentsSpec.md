# Component Catalog

*Inventory of all reusable TSX components in `frontend/src/components/`. Each entry describes the component's purpose, props interface, RPC dependencies (if any), and rebuild status.*

---

## Core Application Components

These components are part of the application shell and should be retained.

### NavBar
- **Purpose:** Sidebar navigation with collapsible expand/collapse, data-driven route list grouped by sequence buckets, section labels derived from route paths
- **Props:** none (reads from UserContext and RPC)
- **RPC dependency:** `public:links` (`fetchNavbarRoutes`) — loads routes on mount and when `userData` changes
- **Status:** Retain — essential application shell component
- **Contains:** `DynamicIcon`, `Login`, `UserContext`

### Login
- **Purpose:** Login/logout widget embedded in the NavBar footer. Shows avatar + display name + credits when logged in, login icon when not
- **Props:** `{ open: bool }` — controls whether text labels are shown (matches NavBar expand state)
- **RPC dependency:** `auth:session` (`fetchInvalidateToken`, `fetchLogoutDevice`) — logout flow
- **External dependency:** `@azure/msal-browser` (Microsoft logout popup), `window.google.accounts.oauth2` (Google revoke)
- **Status:** Retain — essential for auth flow

### BottomBar
- **Purpose:** Footer bar on Home page showing version, hostname, repo links, contact email
- **Props:** `{ info: PublicVarsVersions1 | null }`
- **RPC dependency:** None directly — receives data as prop from Home page
- **Type dependency:** Imports `PublicVarsVersions1` from generated `RpcModels`
- **Status:** Retain — used by Home page

---

## Generic UI Components

Pure UI components with no RPC dependencies. Retain all of these.

### PageTitle
- **Purpose:** Consistent page heading
- **Props:** `{ children: ReactNode }`
- **Status:** Retain

### ColumnHeader
- **Purpose:** Styled table header cell using `columnHeader` typography variant
- **Props:** `{ width?: string, sx?: SxProps, children?: ReactNode }`
- **Status:** Retain

### Notification
- **Purpose:** Snackbar toast notification with severity coloring
- **Props:** `{ open: bool, handleClose: () => void, severity: 'success' | 'info' | 'warning' | 'error', message: string }`
- **Status:** Retain

### EditBox
- **Purpose:** Inline-editable text/number field. Commits on blur or Enter/Tab. Shows "Saved" notification on change.
- **Props:** `{ value: string | number, onCommit: (value) => Promise<void> | void, width?: string | number }`
- **Status:** Retain — canonical row-edit control used across most pages

### DynamicIcon
- **Purpose:** Render any MUI icon by string name. Falls back to `Adjust` icon.
- **Props:** `{ name: string | null | undefined }`
- **Status:** Retain — used by NavBar

---

## Content Components

### MarkdownEditor
- **Purpose:** Split-pane markdown editor with toolbar (bold, italic, headings, links, lists, code) and write/preview toggle
- **Props:** `{ value: string, onChange: (value: string) => void, minHeight?: number, placeholder?: string }`
- **External dependency:** `react-markdown` for preview rendering
- **Status:** Retain — shared by ContentPages and Wiki systems

---

## Media Components

Pure presentation components.

### AudioPreview
- **Purpose:** Inline audio player with play/pause, restart, progress bar, and time display
- **Props:** `{ url: string }`
- **Status:** Retain

### ImagePreview
- **Purpose:** Thumbnail image that opens full-size in new tab on click
- **Props:** `{ url: string }`
- **Status:** Retain

### Postcard
- **Purpose:** Media preview card (image/video/audio) with filename, user display name link, and report flag button
- **Props:** `{ src: string, guid: string, displayName: string, filename: string, onReport: () => void, contentType?: string | null }`
- **Note:** Profile link should be updated to use `public_id` and `/me/{public_profile_id}` when rebuilt
- **Status:** Retain — needs route update on rebuild

---

## Storage Components — Rebuild Required

These components need to be rebuilt as pure UI components that receive all data operations through callbacks.

### FileUpload
- **Purpose:** File upload with progress bar, cancel button, and speed display
- **Current Props:** `{ onComplete?: () => Promise<void> | void, path?: string }`
- **Rebuild as:** Pure upload component accepting `onUpload(file: File, path: string) => Promise<void>` callback. The consuming page provides the upload implementation. Progress tracking through callback or event emitter.
- **Status:** Remove — rebuild as callback-driven component

### FolderManager
- **Purpose:** Breadcrumb path display with up-navigation and create-folder functionality
- **Current Props:** `{ path: string, onPathChange: (path: string) => void, onRefresh?: () => Promise<void> | void }`
- **Rebuild as:** Accept `onCreateFolder(path: string) => Promise<void>` callback. Path navigation is already callback-driven (`onPathChange`), just the folder creation needs the same treatment.
- **Status:** Remove — rebuild as callback-driven component

### StorageItemName
- **Purpose:** Three-state inline rename control (display → armed → editing) with error handling and commit/cancel
- **Props:** `{ name: string, allowRename?: bool, onRename: (newName: string) => Promise<void> }`
- **Status:** Retain — already uses callback pattern correctly

---

## Role Assignment Components

### RoleSelector
- **Purpose:** Dual-list picker for single role assignment (available left ↔ selected right)
- **Props:** `{ available: string[], selected: string[], onAdd: (role: string) => void, onRemove: (role: string) => void }`
- **Status:** Retain — will be useful when role system is rebuilt

### RolesSelector
- **Purpose:** Dual-list picker for multi-role assignment with computed available list
- **Props:** `{ allRoles: string[], value: string[], onChange: (roles: string[]) => void, maxHeight?: number }`
- **Status:** Retain — will be useful when role system is rebuilt

---

## Summary

| Component | RPC Dependency | Status |
|---|---|---|
| NavBar | `public:links` (retained) | Keep |
| Login | `auth:session` (retained) | Keep |
| BottomBar | None (type import only) | Keep |
| PageTitle | None | Keep |
| ColumnHeader | None | Keep |
| Notification | None | Keep |
| EditBox | None | Keep |
| DynamicIcon | None | Keep |
| MarkdownEditor | None | Keep |
| AudioPreview | None | Keep |
| ImagePreview | None | Keep |
| Postcard | None | Keep (needs route fix) |
| StorageItemName | None | Keep |
| RoleSelector | None | Keep |
| RolesSelector | None | Keep |
| FileUpload | Needs rebuild | Remove — rebuild as callback-driven |
| FolderManager | Needs rebuild | Remove — rebuild as callback-driven |

### Component Design Pattern
All components receive data operations through callbacks provided by the consuming page. The page owns the RPC call; the component owns the UI. This keeps components portable, testable, and decoupled from the RPC layer.