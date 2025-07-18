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
- PostgresSQL Database
- Discord Bot TheOracleGPT-dev

These items were previously implemented and are on the rebuild roadmap.
- Azure Storage Account (blob and file share)
- OpenAI, LumaAI, BlueSky Social
- OAuth for Google, Discord, Apple

### Technical Details
- Docker buildx creates a WSGI compliant container that Azure Web App can run.
- The project contains a startup.sh which will be executed by the environment on activation.
- The project contains a dev.cmd script that supports `generate`, `start`, `fast`, and `test` subcommands for local development on Windows.
- Environment variables are configured in .env for local work, but are set up as environment variables on the web app.
- You must configure Always On and enable SCM Basic Auth Publishing Credentials for GitHub Actions.
- Recommend using the Azure Web App Container Quickstart configuration.
- Use Deployment Center to configure CI/CD from GitHub Actions post deploy, target build-ready repo.

### Pull Request Testing
GitHub Actions run both the Node and Python test suites whenever a pull request targets the `main` branch. The workflow is defined in `.github/workflows/pr-tests.yml`.

### AI Usage Details
We are building this site primarily using [Codex](https://chatgpt.com/codex). This is the OpenAI coding agent that integrates directly into your repository. It features agentified access to a full suite of command line build and editing tools.

### CLI Utilities
Several helper scripts in the `scripts` directory manage the project database and data entities:
- `database_cli.py` opens an interactive console with shortcuts for common queries. It provides a `help` command for details.
- `run_tests.py` executes various test, generate, and update operations for build automation.
    - Requires `POSTGRES_CONNECTION_STRING` environment variable to function properly.
- `generate_rpc_client.py` generates function accessors for the RPC namespace defining required interface types.
- `generate_rpc_library.py` generates a data entity library for use in the front end.
- `genlib.py` handles common RPC namespace generation functions.
- `dblib.py` handles most of the database querying operations.

### RPC Response Views
Responses support a simple view suffix in the URN:
`urn:{domain}:{sub}:{func}:{ver}:view:{context}:{variant}`. Each handler
parses these values and applies the appropriate transform after calling the
service function. When no view section is supplied the handler inserts the
default `:view:default:1` suffix which leaves the payload unchanged.

For example `urn:admin:vars:get_hostname:1:view:discord:1` returns a
Discord-friendly hostname string while `urn:admin:vars:get_hostname:1`
returns `urn:admin:vars:hostname:1:view:default:1` with the raw payload.
