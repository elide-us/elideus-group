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
- OAuth2 Microsoft Identity - In progress
- Discord Bot TheOracleGPT-dev

These items were previously implemented and are on the rebuild roadmap.
- Azure Storage Account (blob and file share)
- OpenAI, LumaAI, BlueSky Social
- SQL Database

### Technical Details
- Docker buildx creates a WSGI compliant container that Azure Web App can run.
- The project contains a startup.sh which will be executed by the environment on activation.
- The project contains a devstart.cmd which will build and execute the project locally (on Windows).
- Environment variables are configured in .env for local work, but are set up as environment variables on the web app.
- You must configure Always On and enable SCM Basic Auth Publishing Credentials for GitHub Actions.
- Recommend using the Azure Web App Container Quickstart configuration.
- Use Deployment Center to configure CI/CD from GitHub Actions post deploy, target build-ready repo.

### Pull Request Testing
GitHub Actions run both the Node and Python test suites whenever a pull request targets the `main` branch. The workflow is defined in `.github/workflows/pr-tests.yml`.

### AI Usage Details
We are building this site primarily using [Codex](https://chatgpt.com/codex). This is the OpenAI coding agent that integrates directly into your repository. It features agentified access to a full suite of command line build and editing tools.

### Database Utilities
Several helper scripts in the `scripts` directory manage the project database:
- `create_or_upgrade_database.py` applies the SQL schema found in `db/schema.sql`.
- `interrogate_database_structure.py` prints the current table, column and index details.
- `database_cli.py` opens an interactive console with shortcuts for common queries.
These scripts read the `POSTGRES_CONNECTION_STRING` environment variable so they can run against any configured PostgreSQL server.

### RPC Response Views
RPC methods can return alternate representations using URN suffixes of the form
`urn:{domain}:{subdomain}:{function}:{version}:view:{context}:{variant}`. When a
view suffix is provided, the core method executes and the response is formatted
for the requested context and variant. Requests without a view suffix continue
to return the default models.

The available mappings are exposed via `rpc.get_view_registry()`.
For example, `urn:admin:vars:get_hostname:1:view:discord:1` will return a
Discord-friendly hostname message.
