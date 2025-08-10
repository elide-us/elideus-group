# AGENT Instructions

## Automation and Scripting
- dev.cmd provides different build workflows, use this to model required actions for testing and building
- run_tests.py is the central testing script, use this to model required actions for testing and building
- There are utiliti
- mssql_cli.py and msdblib.py contain functions for Azure SQL database, schema, and data maintenance and management, use this to model any required database interactions
- postgres_cli.py and pgdblib.py are the deprecated postgres database management utilities. These scripts should be avoided as the Postgres backend does not exist
- Consider possible impact to Dockerfile and buildx process, there is no test coverage for this portion of the build, so care must be taken to ensure stability

## Coding Standards
- Python scripts use 2-spaces for indentation
- TypeScript files use 4-space tabs for indentation
- Ensure all test and automation scripts and documentation are updated in line with changes

## Database Management
- /scripts folder contains a record of versions and database schema iterations, when changes are requested, generate a new schema file using "schema dump" process from mssql_cli.py.
- When data loads are required a .sql script is preferred. Human developer will import provided schema and data files using mssql_cli.py.

## Testing Details
- Always run RPC generation scripts before running tests
- Run npm lint, npm type-check, npm test for frontend tests
- Run pytest for Python/FastAPI server tests (/tests folder)

## React Styling
- Use ElideusTheme to apply component styling with variants
- Update theme.d.ts when appropriate

## Tech Stack
This project uses the following technologies currently:
- Node 18/React/TypeScript::Front end web app
- FastAPI on Python 3.12::Back end RPC server
- Docker::WSGI Compliant Container

## Module Initialization
 - `server/modules/__init__.py` auto-loads classes from files named `*_module.py` and attaches each instance to `app.state` using the file name without the `_module` suffix. `db_module.py` becomes `app.state.db`.
 - When other modules depend on the database they should retrieve it from `app.state.db` and await `on_ready()` before use.
- Modules inherit from `BaseModule` and should:
  - call `super().__init__(app)` in `__init__`
  - during `startup`, fetch dependencies from `app.state`, await their `on_ready()` methods, perform setup, and call `mark_ready()` when initialization completes
  - expose any required helpers on `app.state` if other modules need them
- Consumers should await `on_ready()` for any module they depend on to ensure startup ordering.

## File Structure:
### **PYTHON:**
- / folder contains solution build and test automation, configuration and main entry point to FastAPI server
- server/ the FastAPI server, modules and lifespan, helpers and routes
- rpc/ folder contains the Pydantic models, handlers, and services modules
### **REACT:**
- frontend/ folder contains the ReactTS site, this gets built into /static
### **SPECIAL:**
These folders are not part of the server app and need to calculate ROOT for module imports
- tests/ folder contains unit testing and process testing scripts
- scripts/ folder contains RPC to TS generation and testing automation


