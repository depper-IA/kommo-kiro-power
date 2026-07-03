# Leads Workflow

## Creating Leads

When creating leads, follow this order:

1. **List pipelines** first to identify the correct `pipeline_id`
2. **List stages** of the target pipeline to get the `stage_id`
3. **Create the lead** with proper pipeline and stage assignment

### Simple Lead Creation

```
Create a lead named "John Smith - Website Inquiry" in the Sales pipeline, first stage, with price $5000
```

The agent will:
1. Call `list_pipelines` to find "Sales" pipeline ID
2. Call `list_stages` with that pipeline ID
3. Call `create_lead` with name, pipeline_id, stage_id, and price

### Complex Lead Creation (Lead + Contact + Company)

Use `create_lead_complex` when you have full context about the prospect:

```
Create a lead for Maria Garcia from TechCorp, phone +57 310 543 6281, email maria@techcorp.com, in the Enterprise pipeline
```

This creates the lead, contact, and company in a single API call with automatic deduplication.

## Moving Leads Through the Pipeline

```
Move lead 12345 to the "Negotiation" stage
```

The agent will:
1. Get the lead to identify its current pipeline
2. List stages of that pipeline to find "Negotiation" stage ID
3. Call `move_lead_stage`

## Bulk Operations

For updating multiple leads at once:

```
Mark all leads tagged "event-2026" as price $0 and move them to the "Follow-up" stage
```

The agent will:
1. List leads filtered by the tag
2. Resolve the target stage ID
3. Call `bulk_update_leads` with all lead IDs

## Tagging Strategy

Tags are your primary organization tool:

- **Source tags**: `website`, `referral`, `event`, `cold-call`
- **Status tags**: `hot`, `warm`, `cold`, `lost`
- **Campaign tags**: `campaign-q1`, `promo-summer`

```
Add tag "hot" to lead 12345
Remove tag "cold" from lead 12345
```

## Adding Context (Notes & Tasks)

### Notes
```
Add a note to lead 12345: "Called today, interested in premium plan. Follow up Thursday."
```

### Tasks
```
Create a task on lead 12345: "Send proposal" due in 3 days
```

Task due dates are Unix timestamps. The agent will calculate the correct timestamp from relative dates.
