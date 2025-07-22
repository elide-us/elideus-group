## Elideus Group AGENT Alignment Document

### Tech Stack
This project uses the following technologies currently:
- Node 18 (required for atproto)
- React TypeScript + Vite
- ESLint, Vitest, pytest
- Dockerfile + .dockerignore
- FastAPI on Python 3.12
- atproto in React front end
- atproto in Python back end

### Coding Standards:
- Python scripts use 2-space indentation by default
- TypeScript scripts use 4-space TAB indentation by default

### File Structure:
**PYTHON:**
- / folder contains configuration and main.py entry point to FastAPI server
- server/ the FastAPI server, modules and lifespan, helpers and logic
- rpc/ folder contains the Pydantic models, handlers, and services modules
**REACT:**
- frontend/ folder contains the ReactTS site, this gets built into /static
**SPECIAL:** These folders are not part of the server app and need to calculate ROOT for module imports
- tests/ folder contains unit testing and process testing scripts
- scripts/ folder contains RPC to TS generation and testing automation

### Automation
- database_cli + dblib - DB management: View/Import/Export Schema, Backup Data, Version update/tag/commit/push utility
- run_tests - Runs python tests, updates version in CI/CD pipeline to production
- generate_rpc_* - Generates portions of the Pydantic model in Python out to TypeScript libraries

### Database Management Procedures
- Human will import schema files using CLI when changes are requeired
- If data loads are required .sql scripts are preferred

### Actions Build Process:
#### On PR:
- Run generation and testing scripts
#### On Merge:
BUILD:
- Install Node and Python in Actions
- Run generation scripts for TypeScript
- Run Tests for Node and Python
- Run Docker buildx
    - Install Node
    - Build React App
    - Install Python
    - Stage React App
    - Cleanup Workdir
    - Set Entrypoint (expose/startup)

DEPLOY:
- Send to Azure Container Registry
- Update Azure Web App

Ensure all test and automation scripts are updated in line with feature requests.

