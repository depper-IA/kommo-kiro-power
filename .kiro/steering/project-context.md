# kommo-kiro-power — Project Context

## What is this

A **Kiro Power** that connects Kiro IDE to Kommo CRM (formerly amoCRM) via MCP. The Power bundles:
1. A Python MCP server (`kommo_mcp/`) with 30 tools for CRM operations
2. A `POWER.md` with frontmatter, onboarding, and steering file mapping
3. Steering files (`steering/`) with workflow guides loaded on-demand
4. An `mcp.json` with server config for Kiro auto-install

## Goal

Publish this as a public Kiro Power to:
- Help the Kommo/LATAM community manage their CRM from AI agents
- Support the Kiro Ambassador application (community contribution)
- Demonstrate MCP server creation + Power packaging expertise

## Stack

- Python 3.10+ with `mcp` SDK, `httpx`, `python-dotenv`
- OAuth v4 for authentication
- stdio transport (standard for MCP)
- Ruff for linting

## Conventions

- Tool definitions live in `kommo_mcp/tools/` — one file per category
- Each tool file exports `get_{category}_tools()` and `handle_{category}_tool()`
- HTTP client logic is centralized in `kommo_client.py`
- All public-facing text (README, tool descriptions, POWER.md) is in English
- Steering files can be bilingual (EN primary, ES secondary)
- Commit messages follow conventional commits

## Quality Checklist (before release)

- [x] All tools have clear English descriptions in inputSchema
- [x] Every tool in definitions has a matching handler
- [x] POWER.md frontmatter keywords cover all tool categories
- [x] README features table matches actual tools
- [x] oauth_setup.py works standalone
- [x] .env.example has all required vars
- [x] No hardcoded credentials or company references
