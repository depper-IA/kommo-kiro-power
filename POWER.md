---
name: "kommo-crm"
displayName: "Kommo CRM"
description: "Manage leads, contacts, pipelines, tasks, notes, tags, and companies in Kommo CRM directly from your IDE using natural language"
keywords: ["kommo", "crm", "leads", "contacts", "pipelines", "sales", "amocrm", "tasks", "deals", "companies", "chat", "custom-fields", "notes"]
author: "depper-IA"
version: "1.0.0"
---

# Kommo CRM Power for Kiro

Connect your AI agent to [Kommo CRM](https://www.kommo.com) (formerly amoCRM) via the Model Context Protocol. Manage your entire sales pipeline — leads, contacts, companies, tasks, notes, and tags — using natural language from within Kiro.

## Onboarding

### Step 1: Verify Python installation

Ensure Python 3.10+ is installed:

```bash
python --version
```

If not installed, download from [python.org](https://www.python.org/downloads/).

### Step 2: Install the MCP server

```bash
pip install kommo-kiro-power
```

Or install from source:

```bash
git clone https://github.com/depper-IA/kommo-kiro-power.git
cd kommo-kiro-power
pip install -e .
```

### Step 3: Create a Kommo integration

1. Go to your Kommo account → **Settings** → **Integrations** → **Create integration**
2. Copy the **Client ID** and **Client Secret**
3. Set `http://localhost:8080/callback` as the **Redirect URI**

### Step 4: Configure credentials

Create a `.env` file in the kommo-mcp directory:

```env
KOMMO_CLIENT_ID=your_client_id
KOMMO_CLIENT_SECRET=your_client_secret
KOMMO_SUBDOMAIN=your_subdomain
KOMMO_REDIRECT_URI=http://localhost:8080/callback
```

### Step 5: Authenticate via OAuth

Run the authentication script:

```bash
python scripts/oauth_setup.py
```

A browser window will open. Sign in to Kommo and authorize the application. Tokens are saved automatically.

## Available Tools

| Category | Tools |
|----------|-------|
| **Leads** | list, get, create, update, delete, move stage, bulk update |
| **Contacts** | list, get, create, update |
| **Pipelines** | list, create, update, stages (list, create, update) |
| **Tags** | list, add, remove |
| **Tasks** | create, list |
| **Notes** | add note to lead |
| **Chat** | list templates, send message |
| **Companies** | create, list |
| **Custom Fields** | list, create |
| **Advanced** | create lead with contact + company in one call |

## When to Load Steering Files

- Managing leads and sales pipeline → `leads-workflow.md`
- Organizing pipelines and stages → `pipeline-management.md`
- Automating CRM tasks and integrations → `automation-patterns.md`

## Best Practices

- Always list pipelines first to get valid IDs before creating leads
- Use `create_lead_complex` when you need to create a lead with its associated contact and company in one operation
- Tags are resolved by name — if a tag doesn't exist, it will be created automatically
- The server rate-limits to 5 requests/second to respect Kommo's API limits
- Tokens refresh automatically — no manual intervention needed after initial OAuth setup
