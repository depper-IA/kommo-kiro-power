# Skill Registry — kommo-kiro-power

Generated: 2026-07-02

## Project Conventions

| File | Purpose |
|------|---------|
| `.kiro/steering/project-context.md` | Project context, stack, conventions |

## Hooks

| Hook | Trigger | Action |
|------|---------|--------|
| lint-python | fileEdited `**/*.py` | runCommand: `python -m ruff check --fix .` |
| validate-power-md | fileEdited `POWER.md` | askAgent: verify frontmatter + steering refs |
| sync-readme | fileCreated `kommo_mcp/tools/*.py` | askAgent: update README + POWER.md |
| review-tool-schema | fileEdited `kommo_mcp/tools/*.py` | askAgent: verify schema↔handler consistency |

## Compact Rules

### Python MCP Server
- Entry point: `kommo_mcp/__main__.py` → asyncio + stdio_server
- Tools: one file per category in `kommo_mcp/tools/`
- Each file: `get_{cat}_tools()` returns `list[types.Tool]`, `handle_{cat}_tool()` dispatches
- Client: `kommo_client.py` centralizes all HTTP + OAuth + retry logic
- Lint: `ruff check .` and `ruff format .`

### Kiro Power Structure
- `POWER.md`: frontmatter (name, displayName, description, keywords, author, version) + onboarding + steering map
- `mcp.json`: mcpServers config with env vars as `${VAR_NAME}`
- `steering/`: workflow guides loaded on-demand by keyword match
- All public text in English; steering can be bilingual

### Release Quality
- Every tool definition MUST have matching handler
- inputSchema required fields MUST match handler params
- POWER.md keywords MUST cover all tool categories
- No hardcoded credentials; all secrets via .env
