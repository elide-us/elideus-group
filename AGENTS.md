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
- / folder contains configuration and main.py entry point to FastAPI server
- frontend/ folder contains the ReactTS site, this gets built into /static
- rpc/ folder contains the Pydantic models, handlers, and services modules
- scripts/ folder contains RPC to TS generation and testing automation
- tests/ folder contains unit testing and process testing scripts

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

