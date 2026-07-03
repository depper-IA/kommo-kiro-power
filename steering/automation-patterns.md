# Automation Patterns

## Common CRM Automation Workflows

Use Kiro + Kommo MCP to automate repetitive CRM tasks directly from your IDE.

## Pattern 1: Lead Intake from External Source

When you receive leads from a form, CSV, or webhook, create them in bulk:

```
Create leads for each of these prospects in the Inbound pipeline:
- Ana López, ana@startup.co, +57 300 111 2233, company: StartupCo
- Carlos Ruiz, carlos@bigcorp.com, +57 311 444 5566, company: BigCorp
```

The agent will use `create_lead_complex` for each, creating contacts and companies automatically.

## Pattern 2: Pipeline Cleanup

Identify and organize stale leads:

```
List all leads in the "Incoming" stage that haven't been updated
Tag them as "needs-attention"
Create a task on each: "Review and qualify or discard" due tomorrow
```

## Pattern 3: Stage-Based Follow-ups

After a demo or meeting, batch-process next steps:

```
For all leads in "Demo Completed" stage:
1. Add note: "Demo completed, awaiting feedback"
2. Create task: "Send follow-up email" due in 2 days
3. Move them to "Follow-up" stage
```

## Pattern 4: Tag-Based Reporting

Use tags to segment and query:

```
How many leads are tagged "hot" in each pipeline?
List all leads tagged "event-2026" with their current stage
```

## Pattern 5: Contact Enrichment

When you learn new information about a contact:

```
Update contact 67890: add phone +57 315 999 8877
Add note to their lead: "New phone number confirmed via WhatsApp"
```

## Pattern 6: Custom Fields for Segmentation

Create custom fields to track specific data:

```
Create a dropdown field "Lead Source" on leads with values: Website, Referral, Event, Cold Call, Social Media
Create a text field "Company Size" on contacts
```

## Integration with Development Workflow

### CRM-Driven Feature Prioritization

```
List all leads tagged "feature-request" and their notes
```

### Client Communication Tracking

```
Add note to lead 12345: "Deployed v2.1 with requested changes. Sent changelog via email."
Move lead to "Delivery" stage
```

### Sprint Planning Context

```
Show me all leads in "Active Development" stage with their custom fields
```

## Rate Limiting Awareness

The Kommo API allows 5 requests/second. The MCP server handles this automatically with:
- Built-in rate limiting (5 req/sec throttle)
- Automatic retry with exponential backoff on 429 responses
- Response caching for pipelines, stages, and custom fields (10 min TTL)

For bulk operations, the server batches requests efficiently. No manual throttling needed.
