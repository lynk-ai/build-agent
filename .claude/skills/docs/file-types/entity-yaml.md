# Entity YAML Reference

Entity YAML files define the features, metrics, join rules, and examples for a single business entity.

{% hint style="info" %}
**First time here?** If you haven't read the other file-type docs yet, start with [knowledge-md.md](./knowledge-md.md) to understand the scoping model, then [task-instructions-md.md](./task-instructions-md.md) for SQL guidance patterns — both are shorter and establish context this file builds on. Come back here when you're ready to model entities.
{% endhint %}

---

## Quick Reference — Feature Types

| Type | What it does | When to use |
|---|---|---|
| `field` | Pulls a column directly from a source table | Any direct attribute — name, status, amount |
| `metric` | Aggregates from a related entity (feature chaining) | Per-entity totals — total revenue, order count |
| `first_last` | Gets the first or last value ordered by another field | Most recent plan, first order date |
| `formula` | Derives a value from other features on the same entity | Ratios, tiers, days-since calculations |

Each type is documented in detail below.

---

## Top-Level Structure

```yaml
name: {entity_name}
description: {one or two sentence description}

key_source: {warehouse_table}    # primary table — defines entity identity
keys:                            # fields that uniquely identify a row
  - {field_name}

features:                        # attributes — see Feature Types below
  - ...

metrics:                         # aggregation logic — see Entity Metrics below
  - ...

related_sources:                 # secondary warehouse tables joined to the key_source
  {table_name}:
    ...

examples:                        # entity-level query examples
  - ...
```

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Entity identifier — used in `entity('name')` queries |
| `description` | Yes | Human-readable summary for agent context |
| `key_source` | Yes | The primary warehouse table (schema.db.table format) |
| `keys` | Yes | List of fields that form the primary key |
| `features` | Yes | List of feature definitions |
| `metrics` | No | List of entity metric definitions |
| `related_sources` | No | Secondary tables for enrichment |
| `examples` | No | Entity-scoped query examples |

---

## Name and Description

When a user asks a question, the agent decides which entities are relevant based on their `name` and `description`. These are the two fields the agent reads first — before looking at features or metrics.

**`name`** is the entity identifier. It appears in queries (`entity('order')`), in relationships, and in metric feature references. Keep it short, lowercase, and unambiguous.

**`description`** is what the agent uses to decide whether this entity is relevant to the question. A vague description means the agent may miss the entity entirely or pick the wrong one. A good description answers:
- What does this entity represent?
- What questions or topics is it used for?

```yaml
# TOO VAGUE — agent has no signal for when to use this
name: order
description: Order data

# GOOD — agent knows what this is and when it applies
name: order
description: >
  A completed purchase transaction. Use this entity for questions about
  revenue, order volume, purchase dates, and product-level sales.
```

```yaml
# TOO VAGUE
name: session
description: Session information

# GOOD
name: session
description: >
  A single user visit to the product. Use this entity for questions about
  engagement, retention, feature usage, and user behavior.
```

{% hint style="warning" %}
**What not to put in `description`**

The description should only explain what this entity represents and what questions it answers. Two things that don't belong here:

- **Filtering rules or SQL instructions** — "always exclude `is_inactive = true` records when analyzing performance" belongs in [task instructions](./task-instructions-md.md), not here.
- **References to other entities** — "use the `player` entity for career aggregates" is navigation guidance, not a description of what this entity is. The agent selects entities based on question relevance, not cross-entity pointers in descriptions.
{% endhint %}

If your project has multiple entities that could answer similar questions (e.g., `order` and `order_item`), the description is how the agent chooses between them. Be explicit about what the entity represents and what questions it answers.

---

## The `source` Field

Every feature (except `formula`) has a `source` field that tells the agent where to get the data. `source` always means "where this data comes from" — it can be a warehouse table or an entity.

| Feature type | `source` can be | Format |
|---|---|---|
| `field` | A warehouse table/view or an entity | `schema.db.table` or entity name |
| `first_last` | A warehouse table/view or an entity | `schema.db.table` or entity name |
| `metric` | An entity only | entity name (e.g., `order`) |
| `formula` | — | No `source` — references features on this entity |

`metric` features require an entity as `source` because they need aggregation logic (`metrics:`) that only exists on entities, not on raw tables.

When `source` is an entity (for `field` and `first_last` features), the join between the two entities must be defined in `entities_relationships.yml`. Specify which join to use with `join_name` if more than one join exists for that entity pair.

---

## Feature Types

### `field` — Direct Column

Pulls a column from a source table without aggregation.

```yaml
- type: field
  name: full_name
  data_type: string
  source: db_prod.public.customer
  description: Customer's full name
  field: full_name
```

```yaml
- type: field
  name: status
  data_type: string
  source: db_prod.public.customer_info
  description: Current account status — 'active', 'churned', or 'trial'
  field: account_status
  join_name: account_id     # use when source is a related_source, not the key_source
```

| Field | Description |
|---|---|
| `name` | Feature name — what users see and query |
| `data_type` | `string`, `number`, `boolean`, `datetime` |
| `source` | The source table this field comes from |
| `field` | The column name in the source table (may differ from `name`) |
| `join_name` | Which join to use when `source` is a `related_source`. Omit if using the key_source. |
| `filters` | Pre-filters applied to the source before retrieving the field. Omit if no filters. |

---

### `metric` — Aggregated Value from a Related Entity

Pulls an aggregated value from a metric defined on a **related entity**. This is feature chaining.

```yaml
- type: metric
  name: total_revenue
  description: Total revenue from all orders placed by this customer
  data_type: number
  source: order
  metric: sum_amount
```

| Field | Description |
|---|---|
| `source` | The related entity whose metric to use (entity name, not a raw table) |
| `metric` | The metric name from the related entity's `metrics:` section |
| `join_name` | Which relationship join to use. Omit to use the default join for this entity pair. |
| `filters` | Pre-filters applied to the related entity before aggregating. Omit if no filters. |

**With filters:**

```yaml
- type: metric
  name: revenue_2025
  description: Total revenue from orders placed in 2025
  data_type: number
  source: order
  filters:
    - type: sql
      sql: "{source}.{order_date} >= '2025-01-01' and {source}.{order_date} <= '2025-12-31'"
  metric: sum_amount
```

```yaml
- type: metric
  name: enterprise_orders_count
  description: Number of orders from enterprise-tier customers
  data_type: number
  source: order
  filters:
    - type: sql
      sql: "{source}.{customer_tier} = 'enterprise'"
  metric: count_orders
```

Filters use a `sql` expression. Reference the entity's fields with `{source}.{field_name}`.

**Important:** For `metric` features, `source` must be an entity name (e.g., `order`), not a raw table name (e.g., `db_prod.core.orders`). The `metric:` you reference is defined in that entity's `metrics:` section — raw tables don't have metrics.

---

### `first_last` — First or Last Value from a Source

Retrieves the first or last value from a set of rows, ordered by a specified field. Useful for "most recent plan", "first order date", "signup source".

```yaml
- type: first_last
  name: first_order_date
  description: Date of the customer's first order
  data_type: datetime
  source: order
  join_name: customer_to_order
  options:
    method: first
    sort_by: order_date
    field: order_date
    data_type: datetime
```

| Option | Description |
|---|---|
| `method` | `first` = smallest sort value; `last` = largest sort value |
| `sort_by` | The field to order rows by before selecting |
| `field` | The field to return from that row |
| `offset` | Optional. Which position to take — `1` returns the first/last row, `2` returns the second-from-first/last, etc. Defaults to `1` if omitted. |

---

### `formula` — Derived Value

Computes a value from other features on the same entity. References other features using `{feature_name}` syntax.

```yaml
- type: formula
  name: days_since_signup
  data_type: number
  description: Number of days since this customer signed up
  sql: DATEDIFF('day', {signup_date}, CURRENT_DATE)
```

```yaml
- type: formula
  name: revenue_per_order
  data_type: number
  description: Average revenue per order for this customer
  sql: CASE WHEN {total_orders} > 0 THEN {total_revenue} / {total_orders} ELSE 0 END
```

Formula features can reference any feature on the same entity — `field`, `first_last`, `formula`, or `metric`. They cannot reference features on other entities.

---

## Entity Metrics

Entity metrics define how to aggregate rows of this entity. They are the targets of metric features on other entities.

```yaml
metrics:
  - name: sum_amount
    description: Total order amount across all rows
    sql: SUM({amount})

  - name: count_orders
    description: Total number of orders
    sql: COUNT({order_id})

  - name: avg_order_value
    description: Average order value
    sql: AVG({amount})
```

| Field | Description |
|---|---|
| `name` | Metric identifier — referenced by `metric(name)` in queries |
| `description` | Explains what it measures and how to use it |
| `sql` | Aggregation SQL expression. References entity features with `{feature_name}`. |

**Entities are the source of truth.** Raw warehouse tables are inputs — they exist to enrich entities, not to be queried directly. Metrics are defined on entities because entities are where business meaning lives. A raw table has columns; an entity has features, definitions, and metrics that the agent can reason about.

If you need a metric on data that currently lives only in a raw table, you have two options:

1. **Create a new entity** from that table — if the table's level of granularity doesn't exist as an entity yet. Define the entity, bring in the fields as features, and add the metric there.

2. **Use an existing entity** — if an entity already exists at the same level of granularity, create a relationship between that entity and the raw table, bring the fields in as features via `related_sources`, and define the metric as a rollup on those features.

In both cases, the metric ends up on an entity — which is the only place the agent can find and use it.

---

## `related_sources`

Declares secondary warehouse tables used by `field` and `first_last` features. Each entry defines the join condition from the entity's `key_source` to the secondary table.

**When should a warehouse table become an entity vs. a `related_source`?**

Start with the question: *what level of granularity does this table represent?*

**Create a new entity** if:
- The table represents a business concept at its own level of granularity — something with real business meaning that you'd want to ask questions about on its own (e.g., `order`, `subscription`, `session`)
- You need to aggregate rows from it — metrics can only be defined on entities, not on raw sources. If you're counting rows, summing a value, or computing an average from this table, it needs to be an entity
- Other entities need to relate to it via the relationship graph

**Use `related_sources`** if:
- The table is an enrichment — it adds columns to an existing entity but doesn't represent a different level of granularity
- It contains no business logic of its own that you'd aggregate or query independently
- You only need `field` or `first_last` features from it — no metrics

**How to pick the `key_source` for an entity:**

A table is the right `key_source` for an entity if it contains *all* instances of the concept and each instance appears exactly once. For a `customer` entity, the `customers` table where every customer has exactly one row is the right `key_source`. Other tables at the same customer level (e.g., a CRM enrichment table with one row per customer) connect as `related_sources`. Tables at a finer granularity (e.g., orders, one row per order per customer) connect as relationships — they can be aggregated up to the customer level via metric features.


```yaml
related_sources:
  db_prod.public.customer_details:
    relationship: one_to_one
    description: Extended customer info including billing address and plan details
    joins:
      - name: customer_id
        default: true
        type: sql
        sql: "{source}.{id} = {destination}.{customer_id}"
```

**Join types for related_sources:**

| Type | Description |
|---|---|
| `sql` | Explicit SQL join condition using `{source}` and `{destination}` |
| `lookup` | Multi-hop join through intermediate tables |

---

## When to Use This File

Create or update an entity YAML file when a concept meets one of these conditions:
1. You're modeling a new business concept the agent should be able to query
2. You're adding or changing a metric, feature, or dimension on an existing entity
3. The agent produces wrong results for a specific entity — field choices, joins, or calculations need fixing

**Examples:**
- "We want the agent to answer questions about orders — revenue, volume, channel performance" → create an `order` entity
- "Users keep asking about customer health but there's no entity for it yet — model `customer` with ARR, NPS, and churn status" → create a `customer` entity
- "Add a new metric to `customer` — total revenue from the last 90 days" → add a filtered metric feature to the existing entity
- "The agent is joining the wrong table for revenue questions — there are two revenue fields and it keeps picking the wrong one" → add entity-level task instructions and improve feature descriptions
- "We onboarded a new data source for product usage — model it as a `session` entity so the agent can answer engagement questions" → create a new entity from the source table

---

## Best Practices

**Write descriptions that tell the agent when to use this entity.** The agent selects entities based on `name` and `description` — a vague description means missed or wrong matches. Answer: what does this entity represent, and what questions should it answer?

**Write feature descriptions that tell the agent when to use a field.** When two date fields exist on an entity (e.g., `created_at` and `completed_at`), the description should state which one to use for filtering — for example, "use this for all date filtering, not `created_at`".

**Define entity metrics before referencing them in metric features on other entities.** Metric features on `customer` that reference `order` metrics depend on those metrics being defined on the `order` entity. Build the source entity first.

**Prefer metric features for cross-entity aggregation.** If you need a per-customer revenue total, define it as a metric feature — not a formula that approximates it. Metric features use the relationship join; formulas do not.

**Use `first_last` for single values from a many-side entity.** If you need "most recent order date" on `customer`, use `first_last` — not a formula. Formulas cannot aggregate across rows.

**Keep `key_source` as the primary grain table.** Enrichment from secondary tables belongs in `related_sources`. The `key_source` defines the entity's identity — one row = one entity instance.

---

## Common Pitfalls

{% hint style="danger" %}
Avoid these common pitfalls when defining entity features and metrics.
{% endhint %}

**Using a raw table name in a metric feature's `source`**
```yaml
# WRONG
- type: metric
  source: db_prod.core.orders    # this is a source table, not an entity
  metric: sum_amount

# RIGHT
- type: metric
  source: order                  # this is the entity name
  metric: sum_amount
```

**Defining metrics on related_sources**
Sources cannot have metrics. If you need to aggregate from a source, create an entity whose `key_source` is that table, define the metrics on the entity, then use a metric feature.

**Circular formula references**
Formula features can only reference features that are already computed at the same level. A formula cannot reference another formula that references it back.

**Missing relationship for a metric feature**
Metric features require a relationship between the two entities in `entities_relationships.yml`. If the relationship does not exist, the metric feature cannot be resolved.

**Defining entity aliases in the entity YAML**
Aliases — the different names business users use to refer to an entity — belong in the entity knowledge file, not here. The entity YAML defines schema, features, and metrics. The knowledge file is where the agent learns how users naturally refer to this entity in questions.

**Putting filtering rules, SQL instructions, or cross-entity references in the entity `description`**
The `description` field is for what the entity represents and what questions it answers — nothing more. Filtering rules like "always exclude `is_inactive = true`" belong in [task instructions](./task-instructions-md.md). Cross-entity pointers like "use the `player` entity for career aggregates" don't belong here either — the agent selects entities based on question relevance, not navigation hints embedded in descriptions.

---

## Full Examples

These examples cover three different companies. Example 1 is Grove (B2B SaaS) — the `customer` entity, which uses metric features to pull subscription data from the `subscription` entity. Example 2 is Bly (e-commerce) — the `order` entity, standalone with its own metrics. Example 3 is Arcadia (mobile gaming) — the `player` entity, which uses metric features from `purchase` and formula-based segmentation. Reading all three shows the same pattern — entity metrics → feature chaining → query examples — in three distinct business contexts.

---

### Example 1 — Grove (B2B SaaS), `customer` entity

The `customer` entity includes metric features from the `subscription` entity (active subscription count and total MRR). The `customer-subscription` relationship must be defined in `entities_relationships.yml` for these features to resolve.

```yaml
name: customer
description: >
  A paying customer account at Grove. Use this entity for questions about ARR,
  churn, plan type, customer tier, NPS, and account health. For subscription-level
  detail (billing cycle, cancellation dates, MRR per subscription), use the subscription entity.

key_source: db_prod.public.customers

keys:
  - id

features:

  - type: field
    name: id
    data_type: number
    source: db_prod.public.customers
    description: Unique customer identifier
    field: id

  - type: field
    name: company_name
    data_type: string
    source: db_prod.public.customers
    description: Customer's company name
    field: company_name

  - type: field
    name: status
    data_type: string
    source: db_prod.public.customers
    description: >
      Account status.
      'active' — paying customer with a current subscription.
      'churned' — previously paying, subscription ended without renewal.
      'trial' — in free trial period, has not yet converted to paid.
    field: account_status

  - type: field
    name: plan_type
    data_type: string
    source: db_prod.public.customers
    description: >
      Subscription plan tier.
      'starter' — entry-level plan, typically SMB customers.
      'growth' — mid-tier plan for scaling teams.
      'enterprise' — full-featured plan for large organizations.
    field: plan_type

  - type: field
    name: arr
    data_type: number
    source: db_prod.public.customers
    description: Annual Recurring Revenue for this account, in USD
    field: arr

  - type: field
    name: nps_score
    data_type: number
    source: db_prod.public.customers
    description: Most recent NPS survey score (0–10). Updated quarterly.
    field: nps_score

  - type: field
    name: first_paid_at
    data_type: datetime
    source: db_prod.public.customers
    description: Timestamp of the customer's first payment — use this for acquisition date, not created_at
    field: first_paid_at

  - type: field
    name: is_test_account
    data_type: boolean
    source: db_prod.public.customers
    description: True if this is a test or internal account — always exclude from analytics queries
    field: is_test_account

  - type: field
    name: is_deleted
    data_type: boolean
    source: db_prod.public.customers
    description: True if this account has been soft-deleted — always exclude from analytics queries
    field: is_deleted

  # Metric features — pulled from the subscription entity via feature chaining
  # Requires the customer-subscription relationship to be defined in entities_relationships.yml
  - type: metric
    name: active_subscription_count
    description: Number of active subscriptions currently held by this customer
    data_type: number
    source: subscription
    filters:
      - type: sql
        sql: "{source}.{status} = 'active'"
    metric: count_subscriptions

  - type: metric
    name: total_mrr
    description: Total Monthly Recurring Revenue from all active subscriptions for this customer, in USD
    data_type: number
    source: subscription
    filters:
      - type: sql
        sql: "{source}.{status} = 'active'"
    metric: total_mrr

  # Formula — ARR-based customer tier for segmentation and reporting
  - type: formula
    name: customer_tier
    data_type: string
    description: >
      ARR-based tier used for segmentation and reporting.
      Enterprise = ARR >= $100K, Mid-Market = $20K–$99K, SMB = below $20K.
    sql: |
      CASE
        WHEN {arr} >= 100000 THEN 'Enterprise'
        WHEN {arr} >= 20000  THEN 'Mid-Market'
        ELSE 'SMB'
      END

metrics:

  - name: count_customers
    description: Total number of customers
    sql: COUNT(*)

  - name: total_arr
    description: Sum of ARR across all customers, in USD
    sql: SUM({arr})

  - name: avg_arr
    description: Average ARR per customer, in USD
    sql: AVG({arr})

  - name: churn_rate
    description: Percentage of customers with status = 'churned'
    sql: AVG(CASE WHEN {status} = 'churned' THEN 1.0 ELSE 0 END) * 100

examples:

  - type: SQL
    name: arr_by_customer_tier
    description: Total ARR and customer count by tier for active customers
    input: What is our ARR by customer tier?
    expected_output: |
      SELECT
        customer_tier,
        metric(total_arr) as arr,
        metric(count_customers) as customers
      FROM entity('customer')
      WHERE status = 'active'
        AND is_test_account = false
        AND is_deleted = false
      GROUP BY customer_tier
      ORDER BY arr DESC;
    tags:
      difficulty: EASY

  - type: SQL
    name: at_risk_customers
    description: >
      Active customers with low NPS and no active subscriptions in the last 60 days —
      churn risk signal. Uses the active_subscription_count metric feature from subscription.
    input: Show me active customers who are at risk of churning this quarter
    expected_output: |
      SELECT
        company_name,
        customer_tier,
        arr,
        nps_score,
        active_subscription_count,
        total_mrr
      FROM entity('customer')
      WHERE status = 'active'
        AND nps_score < 6
        AND active_subscription_count = 0
        AND is_test_account = false
        AND is_deleted = false
      ORDER BY arr DESC;
    tags:
      difficulty: MEDIUM
```

---

### Example 2 — Bly (E-commerce), `order` entity

The `order` entity is standalone — all metrics are computed directly from order-level features. Note that `order_date` is the time field, not `created_at`.

```yaml
name: order
description: >
  A purchase transaction at Bly. Use this entity for questions about revenue,
  order volume, average order value, channel performance, and refund rates.
  For product-level questions (best-selling SKUs, category performance), use the product entity
  joined through order_items.

key_source: db_prod.core.orders

keys:
  - order_id

features:

  - type: field
    name: order_id
    data_type: number
    source: db_prod.core.orders
    description: Unique order identifier
    field: order_id

  - type: field
    name: customer_id
    data_type: number
    source: db_prod.core.orders
    description: ID of the customer who placed this order
    field: customer_id

  - type: field
    name: status
    data_type: string
    source: db_prod.core.orders
    description: >
      Order fulfillment status.
      'completed' — order fulfilled and paid. Use this filter for all revenue analysis.
      'cancelled' — order placed but not fulfilled.
      'refunded' — completed order that was subsequently refunded.
      'pending' — order received but not yet processed.
    field: status

  - type: field
    name: channel
    data_type: string
    source: db_prod.core.orders
    description: >
      Last-click acquisition channel at time of purchase —
      'organic', 'paid_search', 'paid_social', 'email', or 'direct'
    field: channel

  - type: field
    name: gross_amount
    data_type: number
    source: db_prod.core.orders
    description: Order total before discounts and refunds, in USD. Use net_amount for revenue by default.
    field: gross_amount

  - type: field
    name: net_amount
    data_type: number
    source: db_prod.core.orders
    description: Order total after discounts and refunds, in USD. Default revenue field.
    field: net_amount

  - type: field
    name: discount_pct
    data_type: number
    source: db_prod.core.orders
    description: Discount percentage applied to this order (0–100)
    field: discount_pct

  - type: field
    name: order_date
    data_type: datetime
    source: db_prod.core.orders
    description: >
      Date and time the order was placed — use this for all date filtering, not created_at.
    field: order_date

  - type: field
    name: is_test_order
    data_type: boolean
    source: db_prod.core.orders
    description: True if this is a test or internal order — always exclude from revenue and analytics queries
    field: is_test_order

  # First/last feature — primary product category from order_items (many items per order)
  - type: first_last
    name: primary_category
    description: Product category of the highest-value item in this order — use for category-level analysis
    data_type: string
    source: db_prod.core.order_items
    join_name: order_to_items
    options:
      method: last
      sort_by: item_amount
      offset: 1
      field: category
      data_type: string

related_sources:
  db_prod.core.order_items:
    description: Line-item detail for each order — one order has many items
    relationship: one_to_many
    joins:
      - name: order_to_items
        default: true
        type: sql
        sql: "{source}.{order_id} = {destination}.{order_id}"

metrics:

  - name: count_orders
    description: Total number of orders
    sql: COUNT(*)

  - name: sum_net_revenue
    description: Total net revenue across orders, in USD
    sql: SUM({net_amount})

  - name: avg_order_value
    description: Average net order value, in USD
    sql: AVG({net_amount})

  - name: refund_rate
    description: Percentage of orders that were refunded
    sql: AVG(CASE WHEN {status} = 'refunded' THEN 1.0 ELSE 0 END) * 100

examples:

  - type: SQL
    name: net_revenue_by_channel
    description: Net revenue and order count by acquisition channel for the current month
    input: Show me net revenue and order count by channel this month
    expected_output: |
      SELECT
        channel,
        metric(sum_net_revenue) as net_revenue,
        metric(count_orders) as order_count,
        metric(avg_order_value) as aov
      FROM entity('order')
      WHERE status = 'completed'
        AND is_test_order = false
        AND order_date >= DATE_TRUNC('month', CURRENT_DATE)
      GROUP BY channel
      ORDER BY net_revenue DESC;
    tags:
      difficulty: EASY

  - type: SQL
    name: refund_rate_by_channel
    description: >
      Refund rate by acquisition channel — includes both completed and refunded orders
      to compute the percentage correctly.
    input: What is our refund rate by channel?
    expected_output: |
      SELECT
        channel,
        metric(refund_rate) as refund_rate_pct,
        metric(count_orders) as total_orders
      FROM entity('order')
      WHERE status IN ('completed', 'refunded')
        AND is_test_order = false
      GROUP BY channel
      ORDER BY refund_rate_pct DESC;
    tags:
      difficulty: MEDIUM
```

---

### Example 3 — Arcadia (Mobile gaming), `player` entity

This example shows formula-based segmentation (`player_segment` derived from rolling 30-day spend), two metric features from `purchase` (lifetime and filtered), and a MEDIUM query that identifies high-value players at churn risk. The `player-purchase` relationship must be defined in `entities_relationships.yml` for the metric features to resolve.

```yaml
name: player
description: >
  A registered Arcadia player who has completed at least one game session. Use this entity
  for questions about player counts, activity, spend, segmentation, and D7 retention.
  For session-level metrics (session length, level reached), use the session entity.
  For purchase-level detail, use the purchase entity.

key_source: db_game.public.players

keys:
  - player_id

features:

  - type: field
    name: player_id
    data_type: number
    source: db_game.public.players
    description: Unique player identifier
    field: player_id

  - type: field
    name: username
    data_type: string
    source: db_game.public.players
    description: Player's display name
    field: username

  - type: field
    name: install_date
    data_type: datetime
    source: db_game.public.players
    description: >
      Date the player installed the game. Do not use for cohort analysis on players
      who installed before 2022-03-01 — those records have install_date set to the
      migration date. Use the player_cohort entity for pre-migration cohorts.
    field: install_date

  - type: field
    name: last_session_at
    data_type: datetime
    source: db_game.public.players
    description: >
      Timestamp of the player's most recent session. Use this for all activity checks —
      never use is_active, which lags the actual session data by up to 24 hours.
    field: last_session_at

  - type: field
    name: device_type
    data_type: string
    source: db_game.public.players
    description: Primary device type — 'ios' or 'android'
    field: device_type

  - type: field
    name: country
    data_type: string
    source: db_game.public.players
    description: Player's country, derived from install-time IP
    field: country

  - type: field
    name: d7_retained
    data_type: boolean
    source: db_game.public.players
    description: >
      True if the player had a session on exactly day 7 after install.
      Pre-calculated at day 7 and never updated. Use player_cohort for cohort-level D7 rates.
    field: d7_retained

  # Formula — active player flag based on session recency
  - type: formula
    name: is_active_7d
    data_type: boolean
    description: True if this player had a session in the last 7 days. Use this for all active player filters — do not recalculate inline.
    sql: "{last_session_at} >= CURRENT_DATE - INTERVAL '7 days'"

  # Metric features — pulled from the purchase entity via feature chaining
  # Requires the player-purchase relationship to be defined in entities_relationships.yml
  - type: metric
    name: total_spend_usd
    description: >
      Total lifetime spend in USD from real-money purchases (hard currency only).
      Does not include soft currency earned through gameplay.
    data_type: number
    source: purchase
    filters:
      - type: sql
        sql: "{source}.{purchase_currency} = 'USD'"
    metric: sum_net_revenue_usd

  # Filtered metric feature — spend in the last 30 days for the player_segment formula
  - type: metric
    name: spend_last_30_days_usd
    description: Real-money spend in USD over the last 30 days. Basis for the player_segment formula.
    data_type: number
    source: purchase
    filters:
      - type: sql
        sql: >
          {source}.{purchase_currency} = 'USD'
          AND {source}.{purchase_date} >= CURRENT_DATE - INTERVAL '30 days'
    metric: sum_net_revenue_usd

  # Formula — player segment based on rolling 30-day spend (recalculated weekly via batch job)
  - type: formula
    name: player_segment
    data_type: string
    description: >
      Spend-based segment derived from spend_last_30_days_usd.
      Whale = >$100, Dolphin = $10–$100, Minnow = <$10 with ≥1 purchase, Non-payer = $0.
      Recalculated weekly by batch job — may be up to 7 days stale. Always use this feature
      for segment filtering; never recalculate manually from total_spend_usd.
    sql: |
      CASE
        WHEN {spend_last_30_days_usd} > 100 THEN 'whale'
        WHEN {spend_last_30_days_usd} >= 10  THEN 'dolphin'
        WHEN {spend_last_30_days_usd} > 0    THEN 'minnow'
        ELSE 'non_payer'
      END

metrics:

  - name: count_players
    description: Total number of players
    sql: COUNT(*)

  - name: avg_spend_usd
    description: Average lifetime spend per player in USD
    sql: AVG({total_spend_usd})

examples:

  - type: SQL
    name: active_players_by_device
    description: Count of active players (session in last 7 days) grouped by device type
    input: How many active players do we have by device type?
    expected_output: |
      SELECT
        device_type,
        metric(count_players) as active_players
      FROM entity('player')
      WHERE last_session_at >= CURRENT_DATE - INTERVAL '7 days'
      GROUP BY device_type
      ORDER BY active_players DESC;
    tags:
      difficulty: EASY

  - type: SQL
    name: whale_churn_risk
    description: >
      Whale players with no session in the last 14 days — highest-value segment showing
      early lapse signal. Filters on player_segment formula and last_session_at.
    input: Show me whale players who haven't played in the last 14 days
    expected_output: |
      SELECT
        player_id,
        username,
        country,
        device_type,
        total_spend_usd,
        spend_last_30_days_usd,
        last_session_at
      FROM entity('player')
      WHERE player_segment = 'whale'
        AND last_session_at < CURRENT_DATE - INTERVAL '14 days'
      ORDER BY total_spend_usd DESC;
    tags:
      difficulty: MEDIUM
```
