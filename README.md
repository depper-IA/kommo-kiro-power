# kommo-kiro-power — Kommo CRM Power for Kiro

<!-- mcp-name: io.github.depper-IA/kommo-kiro-power -->

<p align="center">
  <img src="https://img.shields.io/badge/Kiro-Power-blue" alt="Kiro Power" />
  <img src="https://img.shields.io/badge/MCP-Compatible-green" alt="MCP Compatible" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-yellow" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/License-MIT-lightgrey" alt="MIT License" />
</p>

<p align="center">
  <a href="https://glama.ai/mcp/servers/depper-IA/kommo-kiro-power"><img width="380" src="https://glama.ai/mcp/servers/depper-IA/kommo-kiro-power/badges/card.svg" alt="Kommo Kiro MCP server - quality and maintenance score on Glama" /></a>
</p>

Connect AI agents to your **Kommo CRM** (formerly amoCRM) using the [Model Context Protocol](https://modelcontextprotocol.io). Manage leads, contacts, pipelines, tasks, notes, tags, and companies — all from natural language in [Kiro](https://kiro.dev) or any MCP-compatible client.

## Features

| Category | Tools |
|----------|-------|
| **Leads** | list, get, create, update, delete, move stage, bulk update |
| **Contacts** | list, get, create, update |
| **Pipelines** | list, create, update |
| **Stages** | list, create, update |
| **Tags** | list, add, remove (auto-creates if needed) |
| **Tasks** | create, list (with overdue filter) |
| **Notes** | add note to lead |
| **Chat** | list templates, send message |
| **Companies** | create, list |
| **Custom Fields** | list, create (text, select, multiselect, date, etc.) |
| **Advanced** | create lead + contact + company in one call |

## Quick Start

### Install as Kiro Power

1. Open Kiro → Powers panel → **Add Custom Power**
2. Select **Import power from GitHub**
3. Paste: `https://github.com/depper-IA/kommo-kiro-power`
4. Follow the onboarding steps when activated

### Install as standalone MCP

Published on [PyPI](https://pypi.org/project/kommo-kiro-power/) and the [official MCP Registry](https://registry.modelcontextprotocol.io/v0/servers?search=kommo-kiro-power). With [uv](https://docs.astral.sh/uv/) installed, no clone is needed:

```bash
uvx --from kommo-kiro-power kommo-mcp
```

Or from source:

```bash
git clone https://github.com/depper-IA/kommo-kiro-power.git
cd kommo-kiro-power
pip install -e .
```

## Setup

### 1. Create a Kommo Integration

1. Go to Kommo → **Settings** → **Integrations** → **Create integration**
2. Copy the **Client ID** and **Client Secret**
3. Set `http://localhost:8080/callback` as the **Redirect URI**

### 2. Configure Credentials

```bash
cp .env.example .env
# Edit .env with your Kommo integration details
```

### 3. Authenticate (OAuth)

```bash
python scripts/oauth_setup.py
```

A browser opens → sign in to Kommo → authorize → tokens saved automatically.

### 4. Run the MCP Server

```bash
python -m kommo_mcp
# or
kommo-mcp
```

## Usage with Kiro

Once installed as a Power, the server activates automatically when you mention keywords like "kommo", "leads", "pipeline", "crm", or "contacts" in your conversation.

```
"Show me all leads in the Sales pipeline"
"Create a lead for Maria from TechCorp with phone +57 310 543 6281"
"Move lead 12345 to the Negotiation stage"
"List all overdue tasks"
```

## Usage with Other MCP Clients

Add to your `claude_desktop_config.json`, `opencode.json`, or equivalent:

```json
{
  "mcpServers": {
    "kommo": {
      "command": "uvx",
      "args": ["--from", "kommo-kiro-power", "kommo-mcp"],
      "env": {
        "KOMMO_SUBDOMAIN": "your_subdomain",
        "KOMMO_ACCESS_TOKEN": "your_access_token"
      }
    }
  }
}
```

## Architecture

```
kommo-kiro-power/
├── plugin.json           # Kiro Power manifest (Agent Plugins format)
├── POWER.md              # Legacy Kiro Power metadata + onboarding
├── mcp.json              # MCP server config for Kiro
├── server.json           # Official MCP Registry metadata
├── skills/               # Workflow guides loaded on-demand
│   ├── leads-workflow/SKILL.md
│   ├── pipeline-management/SKILL.md
│   └── automation-patterns/SKILL.md
├── kommo_mcp/            # Python MCP server
│   ├── __main__.py       # Entry point (stdio transport)
│   ├── mcp_server.py     # Server + tool registration
│   ├── kommo_client.py   # HTTP client (OAuth, retry, cache)
│   └── tools/            # Tool definitions + handlers
│       ├── leads.py
│       ├── contacts.py
│       └── pipelines.py
├── scripts/
│   └── oauth_setup.py    # One-time OAuth authentication
├── pyproject.toml        # Package config
└── requirements.txt
```

## Security

- Credentials read from `.env` — never hardcoded
- `.env` is in `.gitignore` — never committed
- OAuth v4 with automatic token refresh
- Rate limiting: max 5 requests/second
- Exponential backoff with jitter on failures
- Response caching for pipelines/stages/fields (10 min TTL)

## Compatibility

- **Python**: 3.10, 3.11, 3.12, 3.13
- **MCP Clients**: Kiro, Claude Desktop, OpenCode, Cursor, Codex
- **Kommo API**: v4

## Privacy

The server runs locally on your machine and talks only to your own Kommo account API. It has no telemetry and sends no data to the author or any third party. See [PRIVACY.md](PRIVACY.md).

## Support

- Bugs and feature requests: [GitHub Issues](https://github.com/depper-IA/kommo-kiro-power/issues)
- Email: [sam@wilkiedevs.com](mailto:sam@wilkiedevs.com)

## License

MIT
