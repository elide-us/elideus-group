# AGENT Instructions

## Automation and Scripting
- dev.cmd provides different build workflows, use this to model required actions for testing and building
- run_tests.py is the central testing module, use this to model required actions for testing and building
- database_cli.py and dblib.py contain functions for database, schema, and data maintenance and management, use this to model any required database interactions
- Consider possible impact to Dockerfile and buildx process, there is no test coverage for this portion of the build, so care must be taken to ensure stability

## Coding Standards
- Python scripts use 2-spaces for indentation
- TypeScript files use 4-space tabs for indentation
- Ensure all test and automation scripts are updated in line with changes

## Database Management
- /scripts folder contains a record of versions and database schema iterations, when changes are requested, generate a new schema file using "schema dump" process from database_cli.py.
- When creating new tables that are not tied to a specific join key (such as user GUID or session GUID), include an id SERIAL PRIMARY KEY field for the default index.
- When data loads are required a .sql script is preferred. Human developer will import provided schema and data files using database_cli.py.

## Testing Details
- Always run RPC generation scripts before running tests
- Run npm lint, npm type-check, npm test for frontend tests
- Run pytest for Python/FastAPI server tests (/tests folder)

## Tech Stack
This project uses the following technologies currently:
- Node 18/React/TypeScript::Front end web app
- FastAPI on Python 3.12::Back end RPC server
- Docker::WSGI Compliant Container

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


