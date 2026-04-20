# Step 4: Entities

With business context and domain context in place, model the entities themselves.

The strategy: build dimension entities first (attributes only, no aggregated metrics), then the fact entity that feeds those metrics, then connect them with relationships, then enrich dimensions with feature chaining.

---

## The Build Order

The `customer` entity needs aggregated metrics like total MRR and active subscription count — but those metrics depend on the `subscription` entity and a relationship between them. Build the relationship graph before enriching dimensions.

**The right order:**
1. Dimension entities — identifiers and attributes, no aggregated metrics yet
2. Fact entities — one row per contract or event, define metrics here
3. Relationships — connect entities
4. Enrich dimension entities with metric features that pull from fact entity metrics
5. Context files — add knowledge and task instructions for each entity

---

## 4a: A Dimension Entity — `customer`

Start with the entity that has pure attributes from a single source, no derived aggregations.

**Location:** `.lynk/default/entities/customer.yml`

```yaml
name: customer

description: Dimension table for Grove customer accounts. One row per account. Covers the full lifecycle from trial through active use to churn.

key_source: db_prod.core.customers

keys:
  - id

features:
  - type: field
    name: id
    data_type: number
    source: db_prod.core.customers
    description: Unique identifier for each customer account
    field: id

  - type: field
    name: company_name
    data_type: string
    source: db_prod.core.customers
    description: The customer's company name
    field: company_name

  - type: field
    name: status
    data_type: string
    source: db_prod.core.customers
    description: Current account status — 'active', 'trial', or 'churned'
    field: status

  - type: field
    name: plan_type
    data_type: string
    source: db_prod.core.customers
    description: Subscription tier — 'starter', 'growth', or 'enterprise'
    field: plan_type

  - type: field
    name: arr
    data_type: number
    source: db_prod.core.customers
    description: Annual recurring revenue in USD for this account. Reflects the most recent contract value.
    field: arr

  - type: field
    name: nps_score
    data_type: number
    source: db_prod.core.customers
    description: Most recent NPS survey score (0–10). Null if no survey response on record.
    field: nps_score

  - type: field
    name: first_paid_at
    data_type: date
    source: db_prod.core.customers
    description: Date the account made its first payment. Null for trial accounts. Use as the cohort start date.
    field: first_paid_at

  - type: field
    name: churn_date
    data_type: date
    source: db_prod.core.customers
    description: Date the account churned. Null if the account is active or in trial.
    field: churn_date

  - type: field
    name: is_test_account
    data_type: boolean
    source: db_prod.core.customers
    description: True if this is an internal or test account. Excluded from all analytics by default.
    field: is_test_account

  - type: field
    name: is_deleted
    data_type: boolean
    source: db_prod.core.customers
    description: True if this account has been deleted. Excluded from all analytics by default.
    field: is_deleted

  - type: formula
    name: customer_tier
    data_type: string
    description: Account size tier derived from ARR — SMB (below $20K), Mid-Market ($20K–$99K), Enterprise ($100K+)
    sql: |
      CASE
        WHEN {arr} >= 100000 THEN 'Enterprise'
        WHEN {arr} >= 20000  THEN 'Mid-Market'
        ELSE 'SMB'
      END

metrics:
  - name: count_customers
    description: Count of customer accounts
    sql: COUNT(*)

  - name: total_arr
    description: Sum of ARR across all customer accounts
    sql: SUM({arr})

  - name: avg_arr
    description: Average ARR per customer account
    sql: AVG({arr})

  - name: churn_rate
    description: Percentage of customers with status 'churned' out of all customers
    sql: "SUM(CASE WHEN {status} = 'churned' THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*), 0)"
```

**Key points:**
- `key_source` is the primary warehouse table — the one whose rows define entity identity.
- `keys` lists the fields that uniquely identify a row in the key_source.
- Formula features reference other features on the same entity using `{feature_name}` syntax.
- Entity `metrics` define aggregation logic. Other entities reference these via metric features.
- `total_mrr` and `active_subscription_count` are not here yet — they depend on `subscription`, which we have not modeled yet.

---

## 4b: A Fact Entity — `subscription`

Fact entities have one row per contract or event. They define the metrics that dimension entities will aggregate.

**Location:** `.lynk/default/entities/subscription.yml`

```yaml
name: subscription

description: Subscription records for Grove customers. One row per subscription contract. A customer can have multiple subscriptions over time — upgrades create new records.

key_source: db_prod.core.subscriptions

keys:
  - subscription_id

features:
  - type: field
    name: subscription_id
    data_type: string
    source: db_prod.core.subscriptions
    description: Unique identifier for the subscription contract
    field: subscription_id

  - type: field
    name: customer_id
    data_type: number
    source: db_prod.core.subscriptions
    description: The customer account this subscription belongs to
    field: customer_id

  - type: field
    name: status
    data_type: string
    source: db_prod.core.subscriptions
    description: Current subscription status — 'active', 'cancelled', 'expired', or 'past_due'
    field: status

  - type: field
    name: billing_cycle
    data_type: string
    source: db_prod.core.subscriptions
    description: Billing frequency — 'monthly' or 'annual'
    field: billing_cycle

  - type: field
    name: amount_cents
    data_type: number
    source: db_prod.core.subscriptions
    description: Contract value in cents for the billing period. Monthly subscriptions store the monthly amount; annual subscriptions store the full year amount.
    field: amount_cents

  - type: field
    name: started_at
    data_type: date
    source: db_prod.core.subscriptions
    description: Date the subscription became active
    field: started_at

  - type: field
    name: current_period_end
    data_type: date
    source: db_prod.core.subscriptions
    description: End date of the current billing period. This is the renewal date for active subscriptions.
    field: current_period_end

  - type: field
    name: cancelled_at
    data_type: date
    source: db_prod.core.subscriptions
    description: Date the customer submitted a cancellation request. Null if not cancelled.
    field: cancelled_at

  - type: formula
    name: mrr
    data_type: number
    description: Normalized monthly revenue in USD. Annual subscriptions divided by 12; monthly subscriptions converted directly.
    sql: |
      CASE
        WHEN {billing_cycle} = 'annual' THEN {amount_cents} / 100.0 / 12
        ELSE {amount_cents} / 100.0
      END

  - type: formula
    name: is_pending_cancellation
    data_type: boolean
    description: True if the subscription is active but has a cancellation scheduled before the next renewal
    sql: |
      CASE
        WHEN {status} = 'active'
          AND {cancelled_at} IS NOT NULL
          AND {current_period_end} > CURRENT_DATE
        THEN TRUE
        ELSE FALSE
      END

metrics:
  - name: count_subscriptions
    description: Count of subscription records
    sql: COUNT(*)

  - name: total_mrr
    description: Total normalized monthly recurring revenue across subscriptions
    sql: SUM({mrr})

  - name: count_pending_cancellation
    description: Count of active subscriptions with a scheduled cancellation
    sql: "SUM(CASE WHEN {is_pending_cancellation} THEN 1 ELSE 0 END)"

  - name: mrr_at_risk
    description: Total MRR from subscriptions scheduled for cancellation at end of current period
    sql: "SUM(CASE WHEN {is_pending_cancellation} THEN {mrr} ELSE 0 END)"
```

**Key points:**
- Formula features derive values that metrics then aggregate. `is_pending_cancellation` is a boolean; `count_pending_cancellation` sums it.
- The `mrr` formula normalizes billing cycle differences so all MRR aggregations are apples-to-apples.
- Metrics are defined here once. The `customer` entity will reference `total_mrr` and `mrr_at_risk` via metric features after relationships are in place.

---

## 4c: Relationships

Relationships are defined in a single file shared across all domains, not in entity files.

**Location:** `.lynk/default/entities_relationships.yml`

```yaml
relationships:
  customer-subscription:
    relationship: one_to_many
    description: Each customer account can have multiple subscription records — one per contract period or plan change
    joins:
    - name: customer_to_subscription
      default: true
      description: Join from customer to all their subscription records
      join_type: left
      type: sql
      sql: '{source}.{id} = {destination}.{customer_id}'
    - name: customer_to_active_subscription
      default: false
      description: Join from customer to active subscriptions only
      join_type: left
      type: sql
      sql: '{source}.{id} = {destination}.{customer_id} AND {destination}.{status} = ''active'''
```

**Key points:**
- The relationship key is `{source}-{destination}` — the first entity is the source (left side of the join), the second is the destination (right side). `customer-subscription` means `{source}` = customer, `{destination}` = subscription in the join SQL.
- Named joins let metric features choose which join to use. `customer_to_active_subscription` filters to active subscriptions before aggregating.
- The `default: true` join is used when a metric feature does not specify a `join_name`.
- One relationship entry covers traversal in both directions — you do not need to define `subscription-customer` separately.

---

## 4d: Feature Chaining — Enrich `customer` with Metrics from `subscription`

With the relationship defined, add metric features to `customer.yml` that aggregate from `subscription`.

Add these to the `features` block in `customer.yml`:

```yaml
  - type: metric
    name: total_mrr
    description: Total MRR from all active subscriptions for this customer
    data_type: number
    source: subscription
    join_name: customer_to_active_subscription
    filters: []
    metric: total_mrr

  - type: metric
    name: active_subscription_count
    description: Number of active subscription contracts for this customer
    data_type: number
    source: subscription
    join_name: customer_to_active_subscription
    filters: []
    metric: count_subscriptions

  - type: metric
    name: mrr_at_risk
    description: MRR from this customer's subscriptions that are scheduled for cancellation
    data_type: number
    source: subscription
    join_name: customer_to_subscription
    filters: []
    metric: mrr_at_risk
```

**The chain, step by step:**

1. `subscription.metrics.total_mrr` = `SUM({mrr})` (defined on the fact entity)
2. `customer.features.total_mrr` → type: `metric`, source: `subscription`, join: `customer_to_active_subscription`, metric: `total_mrr`
3. Result: querying `total_mrr` on `customer` executes the MRR sum scoped to that customer's active subscriptions only

Feature chaining keeps aggregation logic in one place. The `mrr` formula and `total_mrr` metric are defined once on `subscription` and reused by any entity that relates to it.

---

## 4e: Entity Context Files

Each entity gets two context files: a knowledge file and a task instructions file.

### Customer Knowledge

**Location:** `.lynk/default/entities/customer/customer__knowledge.md`

This file answers: *What does this entity represent, and what are the business rules specific to it?*

```markdown
---
type: knowledge
domain: "default"
entity: customer
---

## What This Entity Represents

A customer is a company with a Grove account — from first signup through active use to churn. One row per company. The entity covers the full account lifecycle.

## Key Business Rules

- `status` values: 'active' (paying and in contract), 'trial' (evaluating, not yet paying), 'churned' (previously active, now cancelled)
- Trial accounts have null `arr` and null `first_paid_at` — exclude from revenue analysis unless the user is asking about pipeline or trial conversion
- `arr` reflects the most recently synced contract value — it updates when an account upgrades or downgrades
- The `customer_tier` formula uses the current `arr` value — tier history is not tracked in this entity

## Data Quality Notes

- NPS scores recorded before 2021-06-01 used a different survey tool and may not be directly comparable to recent scores
- `churn_date` is set when status changes to 'churned', not when the subscription contract ends — for the contract end date, query the `subscription` entity
```

### Customer Task Instructions

**Location:** `.lynk/default/entities/customer/customer__task_inst__text_to_sql.md`

This file answers: *What SQL patterns and query rules are specific to this entity?*

```markdown
---
type: task-instructions
domain: "default"
entity: customer
tasks: "text-to-sql"
---

## Filtering by Status

- 'active' = paying customers currently in contract
- 'trial' = evaluating, not yet paying — exclude from revenue analysis unless asked about pipeline or conversions
- 'churned' = past customers — include only when specifically analyzing churn

## Revenue Queries

- Use `arr` for current ARR snapshots
- Use the `total_mrr` metric feature when the user asks about monthly revenue
- Never use `total_paid` — it inflates ARR with one-time professional services fees

## Cohort Queries

- Use `first_paid_at` as the cohort start date, not the account creation date
- Always filter out trial accounts (`status != 'trial'`) when running cohort analysis

## Company Name Matching

- Company names are stored as entered by the customer — casing and punctuation vary
- Use case-insensitive matching when filtering by company name from user input
```

### Subscription Knowledge

**Location:** `.lynk/default/entities/subscription/subscription__knowledge.md`

```markdown
---
type: knowledge
domain: "default"
entity: subscription
---

## What This Entity Represents

A subscription is a contract between Grove and a customer. One row per subscription period. When a customer upgrades or downgrades, the old subscription is closed and a new one is created — so a customer's full history may span multiple subscription records.

## Key Business Rules

- `mrr` normalizes monthly vs. annual billing — use it for all MRR calculations, not `amount_cents` directly
- `is_pending_cancellation` is true when a customer has cancelled but the subscription has not yet expired — these are the accounts in the "MRR at risk" bucket
- To find a customer's renewal date, use `current_period_end` on their active subscription
- `status = 'past_due'` means a payment failed — not a voluntary cancellation

## What Counts as Active

For revenue analysis, `status = 'active'` is the right filter. Do not use `cancelled_at IS NULL` as a substitute — a cancelled subscription can still have `status = 'active'` until `current_period_end` passes.
```

### Subscription Task Instructions

**Location:** `.lynk/default/entities/subscription/subscription__task_inst__text_to_sql.md`

```markdown
---
type: task-instructions
domain: "default"
entity: subscription
tasks: "text-to-sql"
---

## Revenue Calculations

- Always use `mrr` for revenue aggregations — not `amount_cents`
- When the user asks about ARR from subscriptions, multiply `mrr` by 12
- Filter `status = 'active'` for all current revenue queries

## Pending Cancellations

- Use `is_pending_cancellation` to find subscriptions at risk — do not manually check `cancelled_at IS NOT NULL AND status = 'active'`
- Use `mrr_at_risk` metric for the revenue exposure from pending cancellations

## Renewal Queries

- Renewal date = `current_period_end` on active subscriptions
- For upcoming renewals, filter `current_period_end BETWEEN CURRENT_DATE AND CURRENT_DATE + 30`
```

---

## Key Point

Build the fact entity (`subscription`) before enriching the dimension entity (`customer`) with metric features. The metric feature on `customer` references `subscription.metrics.total_mrr` — that metric must exist before the reference is valid. The dependency chain is explicit: `customer` is enriched *by* `subscription` through the relationship. Aggregation logic lives once on the fact entity and is reused by any entity that relates to it.
