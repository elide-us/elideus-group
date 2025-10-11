# Package Maintenance Guide

This guide explains how to review, upgrade, and roll back selective dependency groups for the Elideus Group project when working from a Windows Command Prompt. It complements the automation already present in `dev.cmd`, `run_tests.py`, and the new `scripts/dependency_health.py` helper.

## 1. Preparation

1. Open **Developer Command Prompt for VS** or **Windows Terminal (Command Prompt tab)**.
2. Ensure required tooling is installed and available on `PATH`:
   - `git`, `python`/`py`, and `pip`.
   - `node` and `npm` (Node 18 LTS).
3. Sync to the latest default branch and confirm a clean working tree:
   ```cmd
   git pull
   git status
   ```
4. Create a working branch for dependency maintenance:
   ```cmd
   git checkout -b chore/dependency-review-YYYYMMDD
   ```

## 2. Inventory Existing Dependencies

### 2.1 Interactive overview

Run the interactive helper from the repository root:
```cmd
py scripts\dependency_health.py
```
Key features:
- Lists Python packages from `requirements.txt` and `requirements-dev.txt`.
- Lists Node dependencies from `frontend\package.json`.
- Executes `pip list --outdated` and `npm outdated` on demand.
- Highlights targeted package groups (`MUI`, `ATProto`, `React`, `FastAPI stack`, `async IO helpers`) so upgrades can be scoped to logical bundles.

For a non-interactive snapshot that you can paste into an issue comment:
```cmd
py scripts\dependency_health.py --non-interactive
```
Add `--skip-outdated` when running in limited-network environments to skip `pip list --outdated` and `npm outdated` calls.

### 2.2 Manual indexing (Python)

Use the Python launcher (`py`) to inspect installed versions inside your virtual environment:
```cmd
py -m pip list
py -m pip list --outdated --format=columns
```
To view available versions for a single package (example: `fastapi`):
```cmd
py -m pip index versions fastapi
```
Repeat for each security-critical package: `fastapi`, `uvicorn`, `gunicorn`, `aiohttp`, `asyncpg`, `atproto`, and `python-jose`.

### 2.3 Manual indexing (Node)

From the `frontend` directory:
```cmd
cd frontend
npm ls --depth=0
npm outdated
```
For a focused package family:
```cmd
npm view @mui/material versions --json
npm view @atproto/api versions --json
npm view react versions --json
```
Return to the repository root when finished:
```cmd
cd ..
```

## 3. Planning Selective Upgrades

Only upgrade cohesive sets of packages to minimize regressions.

### 3.1 Node upgrade bundles

| Bundle | Packages | Recommended command |
| --- | --- | --- |
| **MUI & Emotion** | `@mui/material`, `@mui/icons-material`, `@emotion/react`, `@emotion/styled` | `npm install @mui/material@latest @mui/icons-material@latest @emotion/react@latest @emotion/styled@latest`
| **ATProto SDK** | `@atproto/api`, `@atproto/crypto`, `@atproto/identity`, `@atproto/lexicon`, `@atproto/xrpc` | `npm install @atproto/api@latest @atproto/crypto@latest @atproto/identity@latest @atproto/lexicon@latest @atproto/xrpc@latest`
| **React Core** | `react`, `react-dom`, `react-router-dom` | `npm install react@latest react-dom@latest react-router-dom@latest`

Usage notes:
- Run the commands from `frontend`. Add `--save-exact` if a lockfile must pin patch versions manually.
- After installing, inspect the generated `package-lock.json` diff to ensure only the targeted bundle changed.
- Rebuild generated frontend assets only after dependency tests pass (`npm run build`).

### 3.2 Python upgrade bundles

| Bundle | Packages | Recommended command |
| --- | --- | --- |
| **FastAPI runtime trio** | `fastapi`, `uvicorn`, `gunicorn` | `py -m pip install --upgrade fastapi uvicorn gunicorn`
| **Async IO helpers** | `aiohttp`, `aiofiles`, `aioodbc`, `asyncpg` | `py -m pip install --upgrade aiohttp aiofiles aioodbc asyncpg`
| **ATProto client** | `atproto` | `py -m pip install --upgrade atproto`

Usage notes:
- Activate the project’s virtual environment before running upgrades.
- Capture currently installed versions first: `py -m pip freeze > logs\freeze-before.txt`.
- After upgrading, export a comparison snapshot: `py -m pip freeze > logs\freeze-after.txt`.
- If a package introduces breaking changes, revert the bundle and investigate before reattempting.

## 4. Verification Checklist

After each bundle upgrade:

1. **Lockfiles and requirement files**
   - Ensure `frontend\package.json` and `frontend\package-lock.json` updates are limited to the intended packages.
   - For Python, verify `requirements*.txt` only change when you explicitly edit them; otherwise leave them untouched if unpinned.

2. **Static analysis & tests**
   ```cmd
   npm run lint
   npm run type-check
   npm test
   py -m venv .venv && call .venv\Scripts\activate && py scripts\run_tests.py
   ```
   If the project already uses a virtual environment, reuse it instead of creating a new one.

3. **Application smoke tests**
   - Launch the backend: `py main.py` (or via Docker if applicable).
   - Launch the frontend dev server: `npm run dev` (inspect login/auth flows touched by the upgrade bundle).

4. **Security audits**
   ```cmd
   npm audit
   py -m pip install --upgrade pip
   py -m pip install pip-audit
   py -m pip_audit
   ```
   Resolve or document high-severity findings before closing the maintenance task.

## 5. Rolling Back Changes

If an upgrade causes regressions:

1. Restore specific files from Git:
   ```cmd
   git checkout -- frontend\package.json frontend\package-lock.json
   git checkout -- requirements.txt requirements-dev.txt
   ```
2. To discard all local changes in the branch:
   ```cmd
   git reset --hard HEAD
   git clean -fd
   ```
3. If a commit was already made, revert it:
   ```cmd
   git log --oneline
   git revert <commit-sha>
   ```
4. Use `git reflog` to recover previous states if you accidentally reset the branch.

## 6. Documenting and Merging

1. Summarize upgrade details in `ARCHITECTURE.md` or team notes if behavior changes.
2. Commit with clear scope (one bundle per commit when possible):
   ```cmd
   git add frontend\package.json frontend\package-lock.json
   git commit -m "chore(frontend): upgrade mui bundle"
   ```
3. Run `git status` to confirm a clean tree before opening a pull request.
4. Use `make_pr` tooling or the standard GitHub flow to create the PR. Include:
   - A changelog of bundles upgraded.
   - Test evidence (`npm lint`, `npm test`, `pytest`).
   - Notes about outstanding advisories or pinned packages.

## 7. Ongoing Maintenance Cadence

- Perform a dependency triage every two weeks, or sooner if security advisories are published.
- Use Renovate (configured in `renovate.json`) as an alerting source but continue to batch manual upgrades into the bundles listed above.
- Track upstream change logs for `fastapi`, `atproto`, and `@mui/*` packages to anticipate breaking changes.

By following these steps, you can confidently maintain the project’s dependency stack, ship security fixes promptly, and keep rollback procedures ready whenever regressions appear.
