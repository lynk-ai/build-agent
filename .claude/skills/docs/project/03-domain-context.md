# Step 3: Domain Context

With domains defined, create the rules and guidance that apply to every query in each domain.

This step produces three files: domain-wide SQL rules that apply to every text-to-sql query, a clarification policy that controls when the agent asks follow-up questions, and an output format that controls how results are presented.

---

## Why Domain Context Before Entities?

Domain context is a multiplier. Every entity you model later inherits these rules — the SQL standards apply to all queries, the clarification policy governs every response, and the knowledge baseline compounds with entity-level context at query time.

Getting domain context right before modeling entities means entity files only need to cover what is unique to that entity. The domain does the heavy lifting for everything shared.

---

## 3a: Domain Task Instructions

**Location:** `.lynk/default/domain_context/default__task_inst__text_to_sql.md`

This file answers: *What SQL rules apply to every query in this domain?*

Anything true for all entities belongs here. Entity task instructions only need to cover what is specific to that entity.

```markdown
---
type: task-instructions
domain: "*"
tasks: "text-to-sql"
---

# SQL Generation Rules

## Always Apply

- Always exclude test accounts: filter `is_test_account = false` unless the user explicitly asks about test accounts
- Always exclude deleted accounts: filter `is_deleted = false` unless explicitly told otherwise
- Use `arr` as the revenue metric. Never use `total_paid` — it includes one-time professional services fees that inflate revenue

## Time and Fiscal Year

- The fiscal year starts February 1. Q1 = Feb–Apr, Q2 = May–Jul, Q3 = Aug–Oct, Q4 = Nov–Jan
- When filtering by quarter, use the fiscal definition above — not calendar quarters
- For cohort analysis, use `first_paid_at` as the customer start date, not the account creation date

## Query Patterns

- When asked about revenue trends, default to monthly granularity unless the user specifies otherwise
- Plan type values in the data are lowercase: 'starter', 'growth', 'enterprise' — filter accordingly
- For churn calculations, use the `churn_rate` metric on the `customer` entity directly — do not derive churn from subscription cancellation counts
```

**What to put in domain task instructions:**
- Default filters that apply to most queries (exclusions for test and deleted records)
- The canonical revenue metric and which fields to avoid
- Date and calendar conventions (fiscal year, cohort start date)
- Preferred query patterns when multiple approaches exist and one is correct

**What to leave out:**
- Entity-specific SQL patterns (join nuances, entity-specific filters) — those go in entity task instructions
- Business definitions and context — those go in knowledge files
- Output formatting — that goes in the output format behavior file

---

## 3b: Clarification Policy

**Location:** `.lynk/default/agent/clarification_policy.md`

This file answers: *When should the agent ask a follow-up question instead of running a query?*

```markdown
---
type: behavior
kind: clarification_policy
domain: "*"
---

## When to Ask for Clarification

- If the user asks about "revenue" without specifying ARR, MRR, or a time period, ask which metric they want and for what period
- If the user asks about "active customers" without context, ask whether they mean `status = 'active'` or activity-based (logged in recently) — the two definitions give different counts
- If the user asks for a trend or change over time without a date range, ask for the time period before running

## When to Proceed Without Asking

- If the user names a specific plan type, entity, or metric — proceed
- If the question is unambiguous given the glossary and knowledge context — proceed
- If the user is asking for a simple count or list with no time constraints — proceed with reasonable defaults and state what was assumed

## Clarification Question Format

- Ask one question at a time — do not bundle multiple clarifications into a single message
- Keep it short: one sentence with the options available
- Do not explain why you are asking
```

**What goes here:**
- Specific ambiguities that recur in this domain (time periods, metric definitions, "active" meaning)
- Explicit rules for when to proceed without asking — this prevents over-asking on simple questions
- Format guidance for how clarification questions should be phrased

---

## 3c: Output Format

**Location:** `.lynk/default/agent/output_format.md`

This file answers: *How should results be presented?*

```markdown
---
type: behavior
kind: output_format
domain: "*"
---

## Tone

Professional and data-oriented. Write as a data analyst presenting findings to a business stakeholder — clear, specific, no hedging.

## Tables

When responding with a table:
- Add a short title (5 words or fewer) above the table
- When displaying counts or revenue figures, show percentage of total alongside the values
- After the table, add 2–3 key observations labeled "Observations" — one sentence each, leading with what is notable

## Data Notes

At the end of each response that includes a table, add a brief "Data notes" line covering:
- The filters applied (e.g., "Excluding test accounts and deleted records")
- The time range if one was applied
- The metric definition used if it could be ambiguous (e.g., "Revenue = ARR, excluding professional services fees")

## What to Avoid

- Do not add disclaimers about AI accuracy — present results confidently
- Do not suggest that users verify results unless the entity knowledge file notes a known data quality issue
```

**What goes here:**
- Tone and professional register for this audience
- Table formatting requirements (title, percentage of total, post-table observations)
- What metadata to always include at the end (filters, time range, metric definition)
- Explicit exclusions that apply to this audience

---

## Key Point

Domain task instructions are for query generation — they make SQL consistent across entities. Behavior files are for communication — they make responses consistent. They serve different layers and do not overlap.

A common mistake is putting output formatting guidance in knowledge files. Knowledge is loaded during query planning; behavior files are loaded during response generation. Formatting guidance in a knowledge file has no effect on how results are presented.
