## TheOracleGPT - RPC Version
Welcome to TheOracleGPT web site repository! We're just getting started, but feel free to follow along!

The following links are for the original site that we're rebuilding and check out Patreon for our project blogs!
* Original TheOracleGPT: https://github.com/elide-us/TheOracle
* Live (Original) Site: https://elideusgroup.com
* Patreon: https://patreon.com/Elideus
* Live (Rebuild) Site: https://elideus-group.azurewebsites.net

### TheOracleGPT - Tech Stack
We'll update this section as we move through the rebuild.
- Azure Web App (Container/Linux B1)
- Azure Container Registry
- GitHub Actions CI/CD Integration
- Python, Node, React, TypeScript, Docker, Vite, ESLint, Vitest, Pytest
- OAuth2 Microsoft Identity
- MSSQL (Azure SQL)
- Discord Bot TheOracleGPT-dev

These items were previously implemented and are on the rebuild roadmap.
- OpenAI, LumaAI, BlueSky Social
- OAuth for Google, Discord, Apple

### Technical Details
- Docker buildx creates a WSGI compliant container that Azure Web App can run.
- The project contains a startup.sh which will be executed by the environment on activation.
- The project contains a dev.cmd script that supports `generate`, `start`, `fast`, and `test` subcommands for local development on Windows.
- Environment variables are configured in .env for local work, but are set up as environment variables on the web app.
- The database provider can be selected with the `DATABASE_PROVIDER` environment variable. The architecture supports multiple providers; currently only `mssql` is implemented.
- You must configure Always On and enable SCM Basic Auth Publishing Credentials for GitHub Actions.
- Deploy the Azure Web App Container Quickstart configuration.
- Use Deployment Center to configure CI/CD from GitHub Actions post deploy, target build-ready repo.

### Pull Request Testing
GitHub Actions run both the Node and Python test suites whenever a pull request targets the `main` branch. The workflow is defined in `.github/workflows/pr-tests.yml`.

### AI Usage Details
We are building this site primarily using [Codex](https://chatgpt.com/codex). This is the OpenAI coding agent that integrates directly into your repository. It features agentified access to a full suite of command line build and editing tools.

### CLI Utilities
Several helper scripts in the `scripts` directory manage the project database and data entities:
- `mssql_cli.py` provides similar features for Azure SQL using the `AZURE_SQL_CONNECTION_STRING` environment variable.
- `run_tests.py` executes various test, generate, and update operations for build automation. It increments the build version directly in the Azure SQL database.
    - Requires `DATABASE_PROVIDER` and the `AZURE_SQL_CONNECTION_STRING` environment variable for MSSQL.
- `generate_rpc_client.py` generates function accessors for the RPC namespace, parsing dispatcher mappings and payload models via the Python AST.
- `generate_rpc_library.py` generates a data entity library for use in the front end.
- `genlib.py` handles common RPC namespace generation functions.
- `msdblib.py` handles most of the mssql querying operations.
  Schema dumps now record NVARCHAR field lengths for accurate
  recreation across environments.

