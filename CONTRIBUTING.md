# 📚 Documentation Overview
Please read the following before diving in:
* AGENTS.md — Context and configuration for Codex agents
* README.md — Technical overview of the architecture and deployment
* SECURITY.md — How security roles, privileges, and bitmask logic work
* RPC.md — Full specification for RPC namespace structure and usage

## 💻 Coding Standards
General Goals
* Test Coverage Target: 85% (measured via Pytest + coverage tools)
Python
* Indentation: 2 spaces
* Type annotations are encouraged for all functions and RPC models
TypeScript
* Indentation: 4-space tabs
* Follow strict type safety patterns (strict: true in tsconfig)

## 🔢 Versioning
We follow a custom interpretation of semantic versioning:
* Major Version — Official Release Milestone (e.g., v1.0)
* Minor Version — New Feature Sets
* Patch Version — Database schema updates
* Build Version — Automation build count

`Format: v1.2.3.45 → Major.Minor.Patch.Build`

## ✅ Contribution Workflow
Before Opening a Pull Request
* 🔄 Sync with main:
Always run git pull origin main before pushing your branch
* 🌱 Use a Feature Branch:
Create branches with clear, descriptive names (e.g., feature/user-profile, bugfix/login-redirect)
* 🧪 Test Your Changes:
Use the dev.cmd script for common workflows:
```
dev generate    # Run RPC generation scripts
dev start       # Run generation, tests, and start FastAPI
dev fast        # Start FastAPI server only
dev test        # Run generation + tests (Python + TypeScript)
```
* 🧰 Use Codex Intelligently:
Codex is your assistant. Use it to:
    * Fill out scaffolding you have created
    * Refactor modules or components to match standards
    * Perform quick peer-reviews for test coverage, deprecated feature usage, best practice and common pattern compliance

## ⚠️ Production Guidelines
* 🚫 Never push directly to main
* ✅ Deploy and test in your dev/test instance before PR
* 🐳 Careful with Docker builds — they bypass tests
* 🔐 Security roles must be verified via test coverage
* 🧼 Document any new RPC verbs or schema changes

## 🤝 Code of Conduct
We value contributors who:
* Share clean, tested code
* Respect the existing architecture and abstractions
* Communicate clearly in issues and PRs
* Ask questions when stuck
* Leave things better than they found them

Be excellent to each other. Misery loves clean merges.
