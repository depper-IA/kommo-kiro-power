# Building a Kiro Power for Kommo CRM: From MCP Server to Published Power

> How I built a 30-tool MCP server and packaged it as a Kiro Power to manage sales pipelines from natural language — all without leaving the IDE.

---

## The Problem

If you run a small business or handle sales alongside development (hello, indie hackers), context-switching between your CRM and your IDE kills productivity. You're writing code, then alt-tabbing to Kommo to check a lead status, then back to code, then back to update a pipeline stage.

What if your AI coding assistant could just... do it for you?

```
"Move lead 12345 to the Negotiation stage and add a note: sent proposal v2"
```

That's what I built.

---

## What is Kiro?

[Kiro](https://kiro.dev) is an agentic IDE built on VS Code that turns prompts into structured requirements, designs, and implementation tasks. One of its key features is **Powers** — packages that give the AI agent instant access to specialized tools and knowledge on-demand.

Powers bundle:
- An MCP (Model Context Protocol) server with tools
- A `POWER.md` with metadata and onboarding instructions
- Steering files with workflow guides

When you mention keywords like "leads" or "pipeline" in conversation, the relevant Power activates automatically.

---

## What is MCP?

The [Model Context Protocol](https://modelcontextprotocol.io) is an open standard for connecting AI agents to external tools. Instead of each AI client implementing custom integrations, MCP provides a universal interface: the agent discovers available tools, understands their schemas, and calls them over a standard transport (stdio or HTTP).

Think of it as USB for AI tools — plug in once, works everywhere.

---

## The Architecture

```
┌─────────────┐     stdio      ┌──────────────┐     HTTPS     ┌─────────────┐
│   Kiro IDE  │ ◄────────────► │  kommo_mcp   │ ◄───────────► │  Kommo API  │
│  (AI Agent) │                │  (Python)    │               │    (v4)     │
└─────────────┘                └──────────────┘               └─────────────┘
                                     │
                                     ├── OAuth v4 (auto-refresh)
                                     ├── Rate limiting (5 req/sec)
                                     ├── Retry with backoff
                                     └── Response caching
```

The MCP server runs locally, communicates with Kiro over stdio, and handles all the complexity of the Kommo API: OAuth token refresh, rate limiting, retries, and caching.

---

## Building the MCP Server

### Project Structure

```
kommo_mcp/
├── __main__.py          # Entry point (asyncio + stdio)
├── mcp_server.py        # Tool registration
├── kommo_client.py      # HTTP client with OAuth + retry
└── tools/
    ├── leads.py         # 16 tools for leads, tags, tasks, notes, chat
    ├── contacts.py      # 4 tools for contact management
    └── pipelines.py     # 10 tools for pipelines, stages, fields, companies
```

### Defining a Tool

Each tool needs a name, description, input schema (JSON Schema), and a handler:

```python
types.Tool(
    name="create_lead",
    description="Create a new lead in Kommo.",
    inputSchema={
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {"type": "string", "description": "Lead name"},
            "price": {"type": "number", "description": "Deal value"},
            "pipeline_id": {"type": "integer"},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
    },
)
```

The AI agent reads this schema and knows exactly how to call the tool. No prompt engineering needed.

### Handling OAuth

Kommo uses OAuth v4 with short-lived tokens. The client handles refresh transparently:

```python
async def _request(self, method, endpoint, **kwargs):
    resp = await self._client.request(method, url, headers=self._headers(), **kwargs)
    
    if resp.status_code == 401:
        await self._refresh_tokens()  # Auto-refresh and retry
        resp = await self._client.request(method, url, headers=self._headers(), **kwargs)
    
    # ... rate limiting, retries, error handling
```

### Rate Limiting

Kommo allows 5 requests/second. Instead of hoping the agent doesn't exceed it, the client enforces it:

```python
async def _rate_limit_wait(self):
    now = time.time()
    self._request_times = [t for t in self._request_times if now - t < 1.0]
    if len(self._request_times) >= 5:
        await asyncio.sleep(1.0 - (now - self._request_times[0]))
    self._request_times.append(time.time())
```

---

## Packaging as a Kiro Power

### POWER.md

The heart of a Power is its `POWER.md` — frontmatter tells Kiro when to activate:

```yaml
---
name: "kommo-crm"
displayName: "Kommo CRM"
description: "Manage leads, contacts, pipelines, tasks, notes, tags, and companies in Kommo CRM"
keywords: ["kommo", "crm", "leads", "contacts", "pipelines", "sales", "amocrm"]
author: "depper-IA"
version: "1.0.0"
---
```

When someone mentions "leads" or "pipeline" in their Kiro conversation, the Power loads its tools automatically.

### mcp.json

This tells Kiro how to run the MCP server:

```json
{
  "mcpServers": {
    "kommo": {
      "command": "python",
      "args": ["-m", "kommo_mcp"],
      "env": {
        "KOMMO_CLIENT_ID": "${KOMMO_CLIENT_ID}",
        "KOMMO_SUBDOMAIN": "${KOMMO_SUBDOMAIN}"
      }
    }
  }
}
```

### Steering Files

These are workflow guides loaded on-demand when the user works on specific tasks:

- `leads-workflow.md` — How to create, move, and tag leads
- `pipeline-management.md` — Pipeline and stage organization
- `automation-patterns.md` — Common CRM automation recipes

---

## The Result: 30 Tools in Natural Language

After installation, you can do things like:

```
"List all leads in the Negotiation stage"
"Create a lead for Maria Garcia from TechCorp, phone +57 310 543 6281"
"Tag all cold leads as needs-attention and create follow-up tasks"
"Show me my pipeline structure"
```

The full tool inventory:

| Category | Operations |
|----------|-----------|
| Leads | list, get, create, update, delete, move stage, bulk update |
| Contacts | list, get, create, update |
| Pipelines | list, create, update, stages |
| Tags | list, add, remove |
| Tasks | create, list |
| Notes | add to lead |
| Chat | list templates, send message |
| Companies | create, list |
| Custom Fields | list, create |
| Advanced | create lead + contact + company in one call |

---

## Key Learnings

**1. Input schemas are your documentation.** The AI reads the JSON Schema to understand how to use your tools. Good descriptions = fewer errors.

**2. Caching matters.** Pipelines and stages rarely change. Caching them for 10 minutes reduced API calls by ~40% during typical sessions.

**3. Rate limiting must be server-side.** Don't trust the AI agent to pace itself. The MCP server must enforce limits internally.

**4. OAuth refresh must be invisible.** If the token expires mid-conversation, the user shouldn't notice. Handle it in the HTTP layer.

**5. Steering files are underrated.** They turn a collection of tools into guided workflows. Without them, the agent has tools but no context about best practices.

---

## Try It Yourself

The Power is open source:

🔗 **[github.com/depper-IA/kommo-kiro-power](https://github.com/depper-IA/kommo-kiro-power)**

Install in Kiro:
1. Powers panel → Add Custom Power → Import from GitHub
2. Paste the repo URL
3. Follow the onboarding (OAuth setup)

Or use as a standalone MCP server with any compatible client:

```bash
pip install -e .
python scripts/oauth_setup.py  # One-time auth
python -m kommo_mcp             # Start server
```

---

## What's Next

- Submit to the [Kiro Powers Registry](https://kiro.dev/powers/) for one-click install
- Add webhook support for real-time lead notifications
- Explore integration with n8n for advanced automation workflows

---

*Built with [Kiro](https://kiro.dev) using spec-driven development. The entire Power — from MCP server to steering files — was developed inside Kiro with its agentic workflow.*

---

**Tags**: `#kiro` `#mcp` `#python` `#crm` `#devtools` `#ai`
