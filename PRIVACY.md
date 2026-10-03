# Privacy Policy

Last updated: 2026-10-03

kommo-kiro-power is an open source MCP server that runs locally on your machine.

## What data it handles

- **Kommo credentials** (subdomain, OAuth client ID/secret, access and refresh tokens) that you provide through environment variables or a local `.env` file.
- **CRM data** (leads, contacts, companies, pipelines, tasks, notes, tags) that your AI client requests from your Kommo account.

## Where the data goes

- Requests go directly from your machine to the Kommo API (`https://<your-subdomain>.kommo.com`).
- CRM data returned by Kommo is passed to the AI client you connected (for example Kiro or Claude). How that client processes it is governed by its own privacy policy.
- Refreshed OAuth tokens are written to a local `.env` file.

## What it does not do

- It does not collect telemetry or analytics.
- It does not send any data to the author or to third parties other than Kommo and your AI client.
- It does not persist CRM data. Lookups such as pipelines, stages, fields and tags are cached in memory only while the server process runs.

## Contact

Questions about this policy: [sam@wilkiedevs.com](mailto:sam@wilkiedevs.com) or [GitHub Issues](https://github.com/depper-IA/kommo-kiro-power/issues).
