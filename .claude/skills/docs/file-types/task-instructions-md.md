# Task Instructions File Reference

Task instruction files tell the agent how to execute a specific task — SQL patterns, field choices, default filters, naming conventions, and edge cases. They are loaded only when the agent is performing that specific task; outside of task execution, this context is not loaded.

---

## Frontmatter

```yaml
---
type: task-instructions
domain: "default"        # or "*" for all domains
tasks: "text-to-sql"     # which task this applies to
entity: customer         # optional — omit for domain-wide instructions
---
```

| Field | Values | Description |
|---|---|---|
| `type` | `task-instructions` | Note: hyphen, not underscore |
| `domain` | `"*"`, `"default"`, `"marketing"`, etc. | Which domain this applies to |
| `tasks` | `"text-to-sql"` | Which task this file applies to |
| `entity` | entity name | Optional. Scopes to a specific entity. Omit for domain-wide instructions. |

---

## Scoping

Task instructions scope by domain and optionally by entity, just like knowledge files. Context compounds — both domain-level and entity-level task instructions are loaded when the agent performs the task on that entity.

| Scope | Frontmatter | When it's loaded |
|---|---|---|
| All entities in all domains | `domain: "*"` / `tasks: "text-to-sql"` | Any text-to-sql task |
| All entities in one domain | `domain: "default"` / `tasks: "text-to-sql"` | Any text-to-sql task in this domain |
| Specific entity | `domain: "default"` / `entity: customer` / `tasks: "text-to-sql"` | text-to-sql on the `customer` entity |

---

## Domain-Level Task Instructions

Cover SQL rules that apply to all entities in the domain.

```markdown
---
type: task-instructions
domain: "default"
tasks: "text-to-sql"
---

## Always Do
- Filter deleted accounts: always add `WHERE is_deleted = false` unless the user explicitly asks about deleted accounts.
- Use `created_at` for date filtering, not `updated_at`, unless the question is about updates.

## Query Best Practices
- Prefer specific entities over joined queries when one entity can answer the question.
- When a question involves "last 30 days", use `CURRENT_DATE - INTERVAL 30 DAY` not a hardcoded date.
- Use full status labels ('active', 'churned') not abbreviations.
```

Good domain task instructions cover:
- Default filters that apply to most queries (exclude deleted, filter inactive)
- Date and time conventions
- Entity preference rules (when multiple entities could answer, which to prefer)
- Naming conventions (full labels vs. abbreviations)

---

## Entity-Level Task Instructions

Cover SQL patterns specific to this entity — field gotchas, join nuances, common query structures.

```markdown
---
type: task-instructions
domain: "default"
entity: customer
tasks: "text-to-sql"
---

## Filtering Active Customers
- Use `status = 'active'` to filter current paying customers.
- Do not use `is_active` — that field reflects CRM status, not subscription status.

## Revenue Queries
- `total_revenue` includes refunds. For net revenue, use `net_revenue`.
- Do not sum `total_revenue` across rows — it is already a metric on the customer entity.

## Date Fields
- Use `first_paid_at` for customer acquisition date, not `created_at`.
  `created_at` reflects account creation, which may predate the first payment.
```

Good entity task instructions cover:
- Which fields to use for display vs. filtering — including which features to return to users (names, not internal IDs)
- When to query this entity vs. a related entity
- Features that look simple but have edge cases
- Commonly confused fields and how to choose the right one — and why
- Filters to always apply (or never apply) for this entity

---

## Lynk SQL Syntax Reference

Task instructions are where you put Lynk SQL patterns the agent should follow for this entity.

**Querying an entity:**
```sql
FROM entity('customer')
```

**Using an entity metric:**
```sql
SELECT
  plan_type,
  metric(count_customers) as total_customers
FROM entity('customer')
GROUP BY plan_type
```

**Filtering and grouping:**
```sql
SELECT
  country,
  metric(avg_revenue_per_customer) as avg_revenue,
  metric(count_customers) as customer_count
FROM entity('customer')
WHERE status = 'active'
GROUP BY country
ORDER BY avg_revenue DESC
```

**Feature access** — features are accessed directly by name, no table prefix needed:
```sql
SELECT email, plan_type, total_revenue
FROM entity('customer')
WHERE status = 'active'
ORDER BY total_revenue DESC
LIMIT 10
```

---

## Best Practices

**Lead with default filters.** The most important instructions are the ones that apply to every query — exclude deleted records, exclude test data, use the right date field. Put these first so they're never missed.

**Use feature names, not raw column names.** Task instructions are applied at query time using entity features. Write `status = 'active'` using the feature name `status`, not the underlying column name `account_status` from the warehouse table.

**Keep domain-level instructions short.** Domain-level task instructions load on every query in the domain. Only put rules here that genuinely apply to all entities. Entity-specific guidance belongs in entity-level files.

**Test instructions with evaluations.** After writing task instructions, run evaluations to verify the agent applies them correctly. Ambiguous wording produces inconsistent SQL — evaluations catch this before production.

**Document why, not just what.** "Use `first_paid_at` for acquisition date, not `created_at` — `created_at` includes trial accounts" is more useful than just "use `first_paid_at`". The reason helps the agent apply the rule correctly in edge cases.

**Reference YAML features — don't restate SQL inline.** If a concept has a formula feature or metric in the entity YAML, reference it by name in task instructions. Don't restate the calculation. The entity YAML is the source of truth; task instructions explain when and why to use a feature, not how it's calculated.

---

## Common Pitfalls

{% hint style="danger" %}
Avoid these common pitfalls when writing task instructions.
{% endhint %}

**Putting SQL guidance in knowledge files**
SQL guidance in knowledge files may not be applied when the agent is writing SQL. Put SQL guidance in task instructions.

**Putting business definitions in task instructions**
If a definition belongs in the reasoning step (what does "active customer" mean?), put it in a knowledge file. Task instructions are for execution guidance, not interpretation.

**Omitting entity-level task instructions for complex entities**
If an entity has tricky fields, multiple join paths, or common misuse patterns, it needs entity-level task instructions. Do not assume domain-level instructions are sufficient.

**Defining metrics or calculations inline instead of referencing the YAML**
Don't write "calculate churn rate as `COUNT(CASE WHEN status = 'churned' THEN 1 END) / COUNT(*)`" in a task instruction. Define it as a `churn_rate` entity metric in the `customer` YAML — then the task instruction says "use the `churn_rate` metric." One definition, one place. If the formula changes, you update the YAML and everything stays in sync.

---

## When to Use This File

Create or update a task instructions file when a situation meets one of these conditions:
1. The agent must apply a specific filter, field choice, or date convention by default when querying an entity or domain
2. There are two similar fields where picking the wrong one produces incorrect results
3. The agent correctly understood the question but the generated SQL was wrong — wrong filter, wrong metric, wrong time field, wrong grouping, or wrong feature returned to the user

**Examples:**
- "Every time you query the orders table, filter out internal test orders unless explicitly asked about them" → add a default filter to entity-level task instructions
- "When asked about revenue, always use `net_amount`, not `gross_amount` — gross includes returns and nobody wants that" → add a field preference rule
- "Our fiscal year starts February 1 — when someone says 'this year' or 'Q1', use fiscal dates" → add to domain-level date conventions
- "The `customer` entity has two revenue fields that look the same but behave differently — the agent needs to know which to use and when" → add entity-level field guidance
- "When asked about 'top customers', always order by ARR, not total paid — total paid includes one-time fees" → add an entity-level sorting rule
- "The agent returned `player_id` in results — business users need `username`, not an internal ID" → add a display field rule

---

## When NOT to Use This File

- If it's guidance on when to use an entity or what a metric means → **entity knowledge file**
- If it's a short term or abbreviation the agent should recognize → **glossary file**
- If it's about how responses are formatted or structured → **output format file**
- If it's about when to ask clarifying questions → **clarification policy file**
- If it's feature-level documentation that applies regardless of task → **entity YAML `description` field**

---

## Full Examples

### Example 1 — Grove (B2B SaaS)

This example shows domain-level and entity-level task instructions for Grove. The domain file sets rules that apply to all SQL in the domain; the `customer` entity file adds field-specific guidance that would not be appropriate at the domain level.

**Domain-level task instructions:**

```markdown
---
type: task-instructions
domain: "default"
tasks: "text-to-sql"
---

## Always Do
- Exclude test accounts: always add `is_test_account = false` unless the question is explicitly about test data.
- Exclude deleted accounts: always add `is_deleted = false`.
- Use `first_paid_at` for customer acquisition date, not `created_at`. `created_at` is account creation and may predate the first payment — it includes trial signups that never converted.

## Date Conventions
- When a question refers to "this quarter" or "Q1", use the fiscal quarter. Fiscal year starts February 1 (Q1 = Feb–Apr, Q2 = May–Jul, Q3 = Aug–Oct, Q4 = Nov–Jan).
- For relative date ranges like "last 30 days", use `CURRENT_DATE - INTERVAL '30 days'` — never hardcode a date.
- When a year is mentioned without a quarter (e.g. "2025 performance"), default to the full fiscal year.

## Entity Preference Rules
- For questions about ARR, churn, or customer health, use the `customer` entity.
- For questions about subscription billing cycles, cancellation dates, or MRR per subscription, use the `subscription` entity.
- For questions about individual invoices or payment history, use the `invoice` entity.

## Naming Conventions
- Use full status labels in filters: `status = 'active'`, not `status = 'a'`.
- Use `plan_type` values as they appear in data: 'enterprise', 'growth', 'starter' (all lowercase).
```

**`customer` entity task instructions:**

```markdown
---
type: task-instructions
domain: "default"
entity: customer
tasks: "text-to-sql"
---

## Revenue Fields
- For ARR questions, use the `arr` feature — this is the primary revenue field for Grove.
- Do not use `total_paid` as a proxy for ARR. `total_paid` includes one-time fees and will overstate recurring revenue.
- `mrr = arr / 12`. Do not calculate MRR independently — derive it from `arr`.

## Segmentation
- "Enterprise" means `plan_type = 'enterprise'` — not `customer_tier = 'Enterprise'` and not `company_size = 'large'`. These are different fields with different values.
- "SMB" means `plan_type IN ('starter', 'growth')`, not the `customer_tier` formula.
- When asked about "top customers", order by `arr DESC`, not `total_paid DESC`, unless lifetime value is explicitly requested.

## Churn Queries
- Logo churn: `COUNT(DISTINCT id)` where `status = 'churned'` and `churn_date` falls within the period.
- Revenue churn: `SUM(arr)` where `status = 'churned'` and `churn_date` falls within the period.
- When "churn" is mentioned without qualification, use logo churn and state the assumption in the response.

## Cohort Queries
- For cohort analysis, group by `DATE_TRUNC('month', first_paid_at)`.
- Do not use `created_at` for cohorts — it includes trial signups that never converted to paid.
```

---

### Example 2 — Bly (E-commerce), `order` entity task instructions

```markdown
---
type: task-instructions
domain: "default"
entity: order
tasks: "text-to-sql"
---

## Default Filters
- For revenue questions, always filter to `status = 'completed'` unless the user explicitly asks about cancellations or refunds.
- Always exclude test orders: `is_test_order = false`.

## Revenue Fields
- Use `net_amount` for revenue by default. Only use `gross_amount` if the user explicitly asks for gross revenue.
- `net_amount` is already after discounts and refunds — it is the correct figure for recognized revenue.

## Date Fields
- Use `order_date` for all date filtering, not `created_at`. `order_date` is the time field on this entity.

## Product and Category Queries
- Product-level questions (best-selling products, category performance) require the `product` entity joined through `order_items`. The `order` entity aggregates to order level and does not have individual line items.
- Use the `order-product` relationship defined in `entities_relationships.yml` for this join.

## Repeat Purchase Queries
- For repeat purchase rate, use the `repeat_purchase_rate` metric on the `customer` entity, not an aggregation from the `order` entity.
- Do not calculate repeat purchase rate by grouping the `order` entity by `customer_id` — use the pre-built metric on `customer` which is based on `customer.total_orders`.
```

---

### Example 3 — Arcadia (Mobile gaming), `player` entity task instructions

This example is denser than the SaaS and e-commerce examples because Arcadia data has more pre-calculated fields with non-obvious freshness or scope constraints. Each rule explains why — the reason helps the agent apply it correctly in edge cases.

```markdown
---
type: task-instructions
domain: "default"
entity: player
tasks: "text-to-sql"
---

## Active Player Definition
- Use the `is_active_7d` formula feature to filter active players — it is defined in the `player` entity YAML. Do not write the filter condition inline.
- Do NOT use `is_active` — that field reflects a daily batch refresh and lags actual session data by up to 24 hours. It will undercount DAU for same-day and recent-day queries.

## Timezone and Day Boundaries
- All timestamps are stored in UTC.
- A day runs from UTC midnight to UTC midnight. Always use UTC midnight as the day boundary for DAU and ARPDAU calculations.
- Do not apply local timezone offsets unless the user explicitly requests a specific timezone.

## Player Segmentation
- Always use the `player_segment` feature for segment filtering — do NOT recalculate from `total_spend_usd` at query time.
- `player_segment` is derived from a 30-day rolling spend window computed in the weekly batch job. Manual recalculation from lifetime spend (`total_spend_usd`) uses a different window and will produce different results that break reporting consistency.
- Valid segment values: 'whale', 'dolphin', 'minnow', 'non_payer' (all lowercase).

## Revenue Queries
- Always filter `purchase_currency = 'USD'` before aggregating spend, unless the question explicitly asks for multi-currency results.
- Use `net_revenue_usd` from the `purchase` entity for all revenue calculations — not a gross field. `net_revenue_usd` excludes platform fees and VAT.

## Retention Metrics
- D1, D7, and D30 retention rates are pre-calculated on the `player_cohort` entity — do not re-derive them from session data.
- `d7_retained` on the `player` entity is a boolean pre-calculated at day 7 per player. It correctly answers "did this player return at day 7?" but it is not a cohort-level D7 retention rate.
- For cohort-level retention questions (e.g. "what is our D7 retention for last week's install cohort?"), use the `player_cohort` entity, not `player`.
```
