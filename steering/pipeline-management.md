# Pipeline Management

## Understanding Kommo Pipelines

A pipeline represents a sales process. Each pipeline has ordered stages that leads move through from initial contact to closed deal (or lost).

### Default Pipeline Structure

```
Incoming → Qualified → Proposal → Negotiation → Won
                                                 └→ Lost
```

## Listing Your Pipelines

Always start by listing existing pipelines to understand your CRM setup:

```
Show me all my pipelines and their stages
```

The agent calls `list_pipelines` which returns all pipelines with embedded stages.

## Creating Pipelines

```
Create a new pipeline called "Partnerships"
```

New pipelines start with default stages (Incoming, Won, Lost). You'll want to add custom stages:

```
Add stages "Initial Contact", "Due Diligence", "Contract Review" to the Partnerships pipeline
```

## Creating Stages

When creating stages, consider:

- **Sort order**: Stages are automatically sorted. New stages are appended after existing ones.
- **Color**: Optional hex color for visual distinction in the Kommo UI.

```
Create a stage "Technical Evaluation" in the Enterprise pipeline with color #4CAF50
```

## Pipeline Best Practices

### Keep it simple
- 4-7 stages per pipeline is optimal
- More stages = more friction in moving leads
- Each stage should represent a clear decision point

### Name stages by action needed
- ❌ "Stage 3" — meaningless
- ✅ "Send Proposal" — clear next action

### Separate pipelines by sales type
- **Inbound**: Website → Qualified → Demo → Proposal → Won
- **Outbound**: Prospecting → Connected → Meeting → Proposal → Won
- **Upsell**: Identified → Pitched → Negotiation → Won

## Updating Pipelines and Stages

```
Rename the "Sales" pipeline to "B2B Sales"
Rename stage "Step 1" to "Discovery Call" in the main pipeline
```

## Querying Pipeline Metrics

```
List all leads in the "Negotiation" stage of the B2B Sales pipeline
How many leads are in each stage of my main pipeline?
```
