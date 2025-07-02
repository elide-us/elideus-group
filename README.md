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
- Python, Node, React, TypeScript, Docker, Vite, ESLint

These items were previously implemented and are on the rebuild roadmap.
- Azure Storage Account (blob and file share)
- OpenAI, LumaAI, BlueSky Social, Discord
- OAuth2 Identity
- SQL Database

### Technical Details
- Docker buildx creates a WSGI compliant container that Azure Web App can run.
- The project contains a startup.sh which will be executed by the environment on activation.
- The project contains a devstart.cmd which will build and execute the project locally (on Windows).
- Environment variables are configured in .env for local work, but are set up as environment variables on the web app.
- You must configure Always On and enable SCM Basic Auth Publishing Credentials for GitHub Actions.
- Recommend using the Azure Web App Container Quickstart configuration.
- Use Deployment Center to configure CI/CD from GitHub Actions post deploy, target build-ready repo.

### Build Details
1. Stage repository
2. Log into Azure Container Registry
3. Execute Docker Buildx (and upload)
   1. Create Node Environment
   2. Lint and Type Check
   3. Vite Build
   4. Create Python Environment
   5. Install Python Requirements
   6. Stage Static Output from Node Environment
   7. Make startup.sh executable (chmod +x)
   8. Expose port 8000 (WSGI entry point)
   9. Define Startup Script
5. Deploy container to Azure Web App

### AI Usage Details
We are building this site primarily using [Codex](https://chatgpt.com/codex). This is the OpenAI coding agent that integrates directly into your repository. It features agentified tools that it can use on a virtual command line where it can search your code with grep, list file names with ls and execute build and test steps during its research phase. This does require some additional configuration, I effectively duplicated the build script for the Codex agent so that it is working even with the live output from the build in the virtual workspace. The advanced integration and agentification of the coding tool greatly improves the results, but it does require very careful prompting because it can take upwards of 7-10 minutes to execute each prompt. This is no chat bot, this thing performs a deep research activity for each task you give it, and can even run multiple scenarios if you desire, and you can also run several tasks at the same time.
